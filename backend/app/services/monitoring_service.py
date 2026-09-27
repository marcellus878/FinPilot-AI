from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.context_builder import build_financial_context
from app.agent.monitoring_agent import (
    build_current_live_snapshot,
    extract_or_build_baseline_snapshot,
)
from app.agent.replanning_agent import (
    generate_adaptive_replanning_strategies,
    generate_plan_comparison,
)
from app.financial_engine.monitoring import (
    FinancialChangeItem,
    MonitoringSnapshot,
    PlanComparisonTable,
    ReplanningAssessment,
    ReplanningStrategyOption,
    detect_financial_changes,
    evaluate_replanning_triggers,
)
from app.models.agent_event import AgentEvent
from app.models.financial_plan import FinancialPlan
from app.schemas.monitoring import (
    FinancialChangeSchema,
    GoalImpactSummarySchema,
    MonitoringRunResponse,
    MonitoringSnapshotSchema,
    MonitoringStatusResponse,
    PlanComparisonItemSchema,
    PlanComparisonTableSchema,
    ReplanningAssessmentSchema,
    ReplanningStrategyOptionSchema,
)

logger = logging.getLogger("finpilot.service.monitoring")


def _map_snapshot_to_schema(s: MonitoringSnapshot) -> MonitoringSnapshotSchema:
    return MonitoringSnapshotSchema(
        monthly_income=str(s.monthly_income),
        monthly_essential_expenses=str(s.monthly_essential_expenses),
        monthly_discretionary_expenses=str(s.monthly_discretionary_expenses),
        monthly_total_expenses=str(s.monthly_total_expenses),
        current_savings=str(s.current_savings),
        monthly_debt_payment=str(s.monthly_debt_payment),
        savings_rate=str(s.savings_rate),
        safe_to_spend_daily=str(s.safe_to_spend_daily),
        emergency_runway_months=str(s.emergency_runway_months),
        emergency_runway_status=s.emergency_runway_status,
        financial_health_score=str(s.financial_health_score),
        financial_health_grade=s.financial_health_grade,
        budget_variance=str(s.budget_variance),
        recurring_commitments_monthly=str(s.recurring_commitments_monthly),
        active_goals_count=s.active_goals_count,
        goals_monthly_required=str(s.goals_monthly_required),
        goals_monthly_capacity=str(s.goals_monthly_capacity),
        goals_feasible=s.goals_feasible,
        timestamp=s.timestamp,
    )


def _map_change_to_schema(c: FinancialChangeItem) -> FinancialChangeSchema:
    return FinancialChangeSchema(
        metric=c.metric,
        baseline=str(c.baseline),
        current=str(c.current),
        absolute_change=str(c.absolute_change),
        percentage_change=str(c.percentage_change),
        severity=c.severity,
        source=c.source,
        description=c.description,
    )


def _map_assessment_to_schema(a: ReplanningAssessment) -> ReplanningAssessmentSchema:
    return ReplanningAssessmentSchema(
        replanning_required=a.replanning_required,
        trigger=a.trigger,
        severity=a.severity,
        affected_areas=a.affected_areas,
        reasons=a.reasons,
        recommendations=a.recommendations,
    )


def _map_strategy_to_schema(s: ReplanningStrategyOption) -> ReplanningStrategyOptionSchema:
    return ReplanningStrategyOptionSchema(
        strategy_id=s.strategy_id,
        title=s.title,
        description=s.description,
        adjusted_essential=str(s.adjusted_essential),
        adjusted_savings=str(s.adjusted_savings),
        adjusted_discretionary=str(s.adjusted_discretionary),
        resulting_buffer=str(s.resulting_buffer),
        impact_on_goals=s.impact_on_goals,
        tradeoffs=s.tradeoffs,
    )


def _map_comparison_to_schema(t: PlanComparisonTable) -> PlanComparisonTableSchema:
    items = [
        PlanComparisonItemSchema(
            area=it.area,
            metric=it.metric,
            baseline_value=it.baseline_value,
            proposed_value=it.proposed_value,
            delta=it.delta,
            explanation=it.explanation,
        )
        for it in t.items
    ]
    goals = [
        GoalImpactSummarySchema(
            goal_name=g.get("goal_name", "Goal"),
            previous_contribution=g.get("previous_contribution", "0.00"),
            proposed_contribution=g.get("proposed_contribution", "0.00"),
            timeline_delay_months=g.get("timeline_delay_months", 0),
            status=g.get("status", "on_track"),
        )
        for g in t.affected_goals
    ]
    return PlanComparisonTableSchema(
        items=items,
        summary=t.summary,
        affected_goals=goals,
    )


def get_monitoring_status(db: Session, user_id: uuid.UUID) -> MonitoringStatusResponse:
    """Returns quick monitoring health and status indicators."""
    context = build_financial_context(db, user_id)
    baseline = extract_or_build_baseline_snapshot(context)
    current = build_current_live_snapshot(context)

    changes = detect_financial_changes(baseline, current)
    assessment = evaluate_replanning_triggers(changes, current, baseline)

    crit_count = len([c for c in changes if c.severity == "critical"])
    high_count = len([c for c in changes if c.severity == "high"])

    plan_status = "replanning_required" if assessment.replanning_required else ("needs_attention" if high_count > 0 else "on_track")

    summary_msg = (
        f"Monitoring active. {len(changes)} financial changes observed. "
        f"{'Plan adaptation recommended due to ' + assessment.trigger.replace('_', ' ') if assessment.replanning_required else 'Current plan remains on track.'}"
    )

    return MonitoringStatusResponse(
        has_baseline=True,
        last_monitored_at=datetime.utcnow(),
        plan_status=plan_status,
        replanning_required=assessment.replanning_required,
        critical_changes_count=crit_count,
        high_changes_count=high_count,
        summary_message=summary_msg,
    )


def run_monitoring_cycle(db: Session, user_id: uuid.UUID) -> MonitoringRunResponse:
    """
    Executes a complete monitoring & adaptive replanning diagnostic cycle:
    1. Extracts baseline and live state.
    2. Runs deterministic change detection.
    3. Evaluates replanning triggers.
    4. Generates proposed strategies and before/after comparison if required.
    5. Saves snapshot metadata in active plan and logs AgentEvent records.
    """
    context = build_financial_context(db, user_id)
    baseline = extract_or_build_baseline_snapshot(context)
    current = build_current_live_snapshot(context)
    goals_list = context.get("goals_portfolio", {}).get("goals", [])

    changes = detect_financial_changes(baseline, current)
    assessment = evaluate_replanning_triggers(changes, current, baseline)

    strategies: List[ReplanningStrategyOption] = []
    plan_comp_table: Optional[PlanComparisonTable] = None

    if assessment.replanning_required or len(changes) > 0:
        strategies = generate_adaptive_replanning_strategies(current, baseline, goals_list)
        if strategies:
            plan_comp_table = generate_plan_comparison(
                baseline=baseline,
                proposed_strategy=strategies[0],
                reason="; ".join(assessment.reasons),
                active_goals=goals_list,
            )

    plan_status = "replanning_required" if assessment.replanning_required else ("needs_attention" if any(c.severity == "high" for c in changes) else "on_track")

    ai_explanation = (
        f"**Plan Status: {plan_status.replace('_', ' ').title()}** — {assessment.reasons[0] if assessment.reasons else 'Plan is on track.'} "
        f"Safe-to-spend: ${current.safe_to_spend_daily}/day, Emergency runway: {current.emergency_runway_months} mos."
    )

    # Persist baseline snapshot in active plan if available
    try:
        plan_stmt = select(FinancialPlan).where(FinancialPlan.user_id == user_id, FinancialPlan.is_active == True)
        active_plan = db.scalar(plan_stmt)
        if active_plan:
            current_data = dict(active_plan.plan_data or {})
            current_data["monitoring_baseline"] = {
                "monthly_income": float(current.monthly_income),
                "monthly_essential_expenses": float(current.monthly_essential_expenses),
                "monthly_discretionary_expenses": float(current.monthly_discretionary_expenses),
                "current_savings": float(current.current_savings),
                "monthly_debt_payment": float(current.monthly_debt_payment),
                "safe_to_spend_daily": float(current.safe_to_spend_daily),
                "emergency_runway_months": float(current.emergency_runway_months),
                "emergency_runway_status": current.emergency_runway_status,
                "financial_health_score": float(current.financial_health_score),
                "financial_health_grade": current.financial_health_grade,
                "budget_variance": float(current.budget_variance),
                "recurring_commitments_monthly": float(current.recurring_commitments_monthly),
                "active_goals_count": current.active_goals_count,
                "goals_monthly_required": float(current.goals_monthly_required),
                "goals_monthly_capacity": float(current.goals_monthly_capacity),
                "goals_feasible": current.goals_feasible,
                "last_monitored_at": datetime.utcnow().isoformat(),
            }
            active_plan.plan_data = current_data
            db.commit()
    except Exception as e:
        logger.warning(f"Failed to update monitoring baseline in active plan: {e}")
        db.rollback()

    # Log summary AgentEvent
    try:
        event = AgentEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            event_type="monitoring_cycle_completed",
            responsible_agent="monitoring_agent",
            previous_state={"plan_status": plan_status},
            new_state={
                "changes_count": len(changes),
                "replanning_required": assessment.replanning_required,
                "trigger": assessment.trigger,
                "severity": assessment.severity,
            },
        )
        db.add(event)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to log monitoring AgentEvent: {e}")
        db.rollback()

    return MonitoringRunResponse(
        baseline_snapshot=_map_snapshot_to_schema(baseline),
        current_snapshot=_map_snapshot_to_schema(current),
        changes=[_map_change_to_schema(c) for c in changes],
        assessment=_map_assessment_to_schema(assessment),
        plan_comparison=_map_comparison_to_schema(plan_comp_table) if plan_comp_table else None,
        strategies=[_map_strategy_to_schema(s) for s in strategies],
        ai_explanation=ai_explanation,
        plan_status=plan_status,
    )


def get_detected_changes(db: Session, user_id: uuid.UUID) -> List[FinancialChangeSchema]:
    """Returns detected changes between baseline and current state."""
    context = build_financial_context(db, user_id)
    baseline = extract_or_build_baseline_snapshot(context)
    current = build_current_live_snapshot(context)
    changes = detect_financial_changes(baseline, current)
    return [_map_change_to_schema(c) for c in changes]


def get_replanning_proposal(db: Session, user_id: uuid.UUID) -> Optional[PlanComparisonTableSchema]:
    """Returns the proposed plan comparison table if replanning is needed."""
    context = build_financial_context(db, user_id)
    baseline = extract_or_build_baseline_snapshot(context)
    current = build_current_live_snapshot(context)
    goals_list = context.get("goals_portfolio", {}).get("goals", [])

    changes = detect_financial_changes(baseline, current)
    assessment = evaluate_replanning_triggers(changes, current, baseline)
    strategies = generate_adaptive_replanning_strategies(current, baseline, goals_list)

    if strategies:
        plan_comp = generate_plan_comparison(
            baseline=baseline,
            proposed_strategy=strategies[0],
            reason="; ".join(assessment.reasons),
            active_goals=goals_list,
        )
        return _map_comparison_to_schema(plan_comp)
    return None
