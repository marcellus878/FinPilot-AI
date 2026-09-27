from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.orm import Session

from app.models.agent_event import AgentEvent
from app.models.decision_history import DecisionHistory
from app.models.goal import Goal
from app.schemas.decision_memory import (
    DecisionMemoryCreateSchema,
    DecisionMemoryDriftSchema,
    DecisionMemoryItemSchema,
    ProactiveInsightSchema,
)

logger = logging.getLogger("finpilot.services.decision_memory")


def save_decision_memory(
    db: Session,
    user_id: uuid.UUID,
    data: DecisionMemoryCreateSchema,
) -> DecisionHistory:
    """
    Persists structured decision metadata into PostgreSQL.
    """
    record = DecisionHistory(
        id=uuid.uuid4(),
        user_id=user_id,
        user_action=data.user_action,
        decision=data.decision,
        decision_type=data.decision_type,
        item_name=data.item_name,
        amount=data.amount,
        strategy_selected=data.strategy_selected,
        alternatives_considered=data.alternatives_considered,
        affected_goals=data.affected_goals,
        baseline_metrics=data.baseline_metrics,
        resulting_metrics=data.resulting_metrics,
        assumptions=data.assumptions,
        recommendation_summary=data.recommendation_summary,
        financial_impact=data.financial_impact,
        status=data.status,
    )
    db.add(record)
    
    # Audit log
    event = AgentEvent(
        id=uuid.uuid4(),
        user_id=user_id,
        event_type="decision_memory_saved",
        responsible_agent="DecisionMemoryService",
        previous_state={"action": data.user_action},
        new_state={
            "decision_id": str(record.id),
            "decision_type": data.decision_type,
            "item_name": data.item_name,
            "strategy": data.strategy_selected,
        },
    )
    db.add(event)
    db.commit()
    db.refresh(record)
    return record


def retrieve_relevant_memory(
    db: Session,
    user_id: uuid.UUID,
    query: Optional[str] = None,
    decision_type: Optional[str] = None,
    item_name: Optional[str] = None,
    goal_name: Optional[str] = None,
    limit: int = 10,
) -> List[DecisionHistory]:
    """
    Deterministic retrieval of previous decisions using PostgreSQL queries and indexed fields.
    """
    stmt = select(DecisionHistory).where(DecisionHistory.user_id == user_id)

    if decision_type:
        stmt = stmt.where(DecisionHistory.decision_type == decision_type)

    if item_name:
        stmt = stmt.where(DecisionHistory.item_name.ilike(f"%{item_name}%"))

    if goal_name:
        # Check text match or JSON containment
        stmt = stmt.where(
            or_(
                DecisionHistory.decision.ilike(f"%{goal_name}%"),
                DecisionHistory.user_action.ilike(f"%{goal_name}%"),
            )
        )

    if query:
        q_lower = query.strip().lower()
        # Search across user_action, decision, item_name, strategy_selected
        stmt = stmt.where(
            or_(
                DecisionHistory.user_action.ilike(f"%{q_lower}%"),
                DecisionHistory.decision.ilike(f"%{q_lower}%"),
                DecisionHistory.item_name.ilike(f"%{q_lower}%"),
                DecisionHistory.strategy_selected.ilike(f"%{q_lower}%"),
            )
        )

    stmt = stmt.order_by(desc(DecisionHistory.created_at)).limit(limit)
    results = db.execute(stmt).scalars().all()
    return list(results)


def evaluate_memory_drift(
    db: Session,
    user_id: uuid.UUID,
    decision: DecisionHistory,
) -> DecisionMemoryDriftSchema:
    """
    Compares baseline financial metrics recorded at the time of decision
    against live financial engine state to detect changed circumstances.
    """
    from app.agent.context_builder import build_financial_context
    current_context = build_financial_context(db, user_id)
    baseline = decision.baseline_metrics or {}
    
    current_income = Decimal(str(current_context.get("profile", {}).get("monthly_income", "0.00")))
    current_disposable = Decimal(str(current_context.get("core_metrics", {}).get("disposable_income", "0.00")))
    current_safe_to_spend = Decimal(str(current_context.get("cash_flow", {}).get("safe_to_spend_daily", "0.00")))
    current_runway = Decimal(str(current_context.get("core_metrics", {}).get("emergency_fund_months", "0.00")))
    current_savings = Decimal(str(current_context.get("profile", {}).get("current_savings", "0.00")))

    base_income = Decimal(str(baseline.get("monthly_income", current_income)))
    base_disposable = Decimal(str(baseline.get("disposable_income", current_disposable)))
    base_safe_to_spend = Decimal(str(baseline.get("safe_to_spend_daily", current_safe_to_spend)))
    base_runway = Decimal(str(baseline.get("emergency_runway_months", current_runway)))
    base_savings = Decimal(str(baseline.get("current_savings", current_savings)))

    comparison: Dict[str, Dict[str, Any]] = {
        "monthly_income": {
            "baseline": f"${base_income:,.2f}",
            "current": f"${current_income:,.2f}",
            "delta": f"${(current_income - base_income):,.2f}",
            "changed": abs(current_income - base_income) >= Decimal("50.00"),
        },
        "disposable_surplus": {
            "baseline": f"${base_disposable:,.2f}",
            "current": f"${current_disposable:,.2f}",
            "delta": f"${(current_disposable - base_disposable):,.2f}",
            "changed": abs(current_disposable - base_disposable) >= Decimal("30.00"),
        },
        "safe_to_spend_daily": {
            "baseline": f"${base_safe_to_spend:,.2f}/day",
            "current": f"${current_safe_to_spend:,.2f}/day",
            "delta": f"${(current_safe_to_spend - base_safe_to_spend):,.2f}/day",
            "changed": abs(current_safe_to_spend - base_safe_to_spend) >= Decimal("5.00"),
        },
        "emergency_runway": {
            "baseline": f"{base_runway:.1f} mo",
            "current": f"{current_runway:.1f} mo",
            "delta": f"{(current_runway - base_runway):.1f} mo",
            "changed": abs(current_runway - base_runway) >= Decimal("0.3"),
        },
        "current_savings": {
            "baseline": f"${base_savings:,.2f}",
            "current": f"${current_savings:,.2f}",
            "delta": f"${(current_savings - base_savings):,.2f}",
            "changed": abs(current_savings - base_savings) >= Decimal("100.00"),
        },
    }

    changed_count = sum(1 for v in comparison.values() if v["changed"])
    has_drifted = changed_count > 0

    if changed_count >= 3 or abs(current_income - base_income) >= Decimal("300.00"):
        drift_severity = "high"
    elif changed_count >= 1:
        drift_severity = "medium"
    else:
        drift_severity = "none"

    # Human-readable explanation
    reasons = []
    if current_income > base_income:
        reasons.append(f"Income increased by ${(current_income - base_income):,.2f}/mo")
    elif current_income < base_income:
        reasons.append(f"Income dropped by ${(base_income - current_income):,.2f}/mo")

    if current_safe_to_spend > base_safe_to_spend:
        reasons.append(f"Safe daily spending capacity grew to ${current_safe_to_spend:,.2f}/day")
    elif current_safe_to_spend < base_safe_to_spend:
        reasons.append(f"Safe daily spend tightened to ${current_safe_to_spend:,.2f}/day")

    if current_runway > base_runway:
        reasons.append(f"Emergency runway strengthened to {current_runway:.1f} months")

    if not reasons:
        explanation = "Your financial metrics remain consistent with when this decision was originally evaluated."
    else:
        explanation = (
            f"Your financial circumstances have shifted since this decision: {'; '.join(reasons)}. "
            f"A fresh scenario evaluation is recommended."
        )

    return DecisionMemoryDriftSchema(
        decision_id=str(decision.id),
        decision_type=decision.decision_type,
        item_name=decision.item_name,
        created_at=decision.created_at,
        has_drifted=has_drifted,
        drift_severity=drift_severity,
        metrics_comparison=comparison,
        explanation=explanation,
        can_re_evaluate=True,
    )


def generate_proactive_insights(
    db: Session,
    user_id: uuid.UUID,
) -> List[ProactiveInsightSchema]:
    """
    Synthesizes proactive financial insights from live state, past decisions, and active goals.
    Always grounded in deterministic calculations.
    """
    from app.agent.context_builder import build_financial_context
    context = build_financial_context(db, user_id)
    insights: List[ProactiveInsightSchema] = []

    profile = context.get("profile", {})
    core = context.get("core_metrics", {})
    cash_flow = context.get("cash_flow", {})
    goals = context.get("goals_portfolio", {})
    expenses = context.get("expense_summary", {})
    intel = context.get("spending_intelligence", {})

    income = Decimal(str(profile.get("monthly_income", "0.00")))
    disposable = Decimal(str(core.get("disposable_income", "0.00")))
    safe_daily = Decimal(str(cash_flow.get("safe_to_spend_daily", "0.00")))
    runway = Decimal(str(core.get("emergency_fund_months", "0.00")))
    health_score = Decimal(str(context.get("financial_health_score", {}).get("overall_score", "0.00")))

    # 1. Check past decisions for changed circumstances
    recent_decisions = retrieve_relevant_memory(db, user_id, limit=3)
    for dec in recent_decisions:
        drift = evaluate_memory_drift(db, user_id, dec)
        if drift.has_drifted and drift.drift_severity in ["medium", "high"]:
            item_label = dec.item_name or dec.decision_type.replace("_", " ")
            insights.append(
                ProactiveInsightSchema(
                    id=f"insight-drift-{dec.id}",
                    insight_type="decision_revisit",
                    title=f"Circumstances Changed: {item_label}",
                    description=drift.explanation,
                    severity=drift.drift_severity,
                    related_decision_id=str(dec.id),
                    action_prompt=f"Re-evaluate my previous decision about {item_label}",
                    metric_facts=[
                        {"metric": "Safe Daily Spend", "value": f"${safe_daily:,.2f}/day"},
                        {"metric": "Monthly Surplus", "value": f"${disposable:,.2f}/mo"},
                    ],
                )
            )

    # 2. Goal conflict / capacity insights
    if goals.get("has_conflicts", False):
        shortfall = goals.get("conflict_shortfall", 0.0)
        insights.append(
            ProactiveInsightSchema(
                id=f"insight-goal-conflict-{uuid.uuid4().hex[:8]}",
                insight_type="goal_risk",
                title="Goal Contribution Deficit Detected",
                description=(
                    f"Your active goals require ${goals.get('total_monthly_required', 0.0):,.2f}/month, "
                    f"exceeding your current monthly disposable surplus by ${shortfall:,.2f}/month."
                ),
                severity="high",
                action_prompt="How do I resolve my competing goal conflicts?",
                metric_facts=[
                    {"metric": "Monthly Surplus", "value": f"${disposable:,.2f}"},
                    {"metric": "Goal Requirement", "value": f"${goals.get('total_monthly_required', 0.0):,.2f}"},
                ],
            )
        )

    # 3. Discretionary spending vs goal contribution imbalance
    disc_ratio = Decimal(str(expenses.get("discretionary_ratio", "0.00")))
    if disc_ratio > Decimal("35.00") and goals.get("active_goals_count", 0) > 0:
        insights.append(
            ProactiveInsightSchema(
                id=f"insight-discretionary-{uuid.uuid4().hex[:8]}",
                insight_type="spending_anomaly",
                title="Elevated Discretionary Spend",
                description=(
                    f"Discretionary spending makes up {disc_ratio:.1f}% of your monthly outflows. "
                    f"Reallocating 15% of non-essentials could accelerate your active goal milestones."
                ),
                severity="medium",
                action_prompt="Show me how reducing discretionary spending helps my goals",
                metric_facts=[
                    {"metric": "Discretionary Share", "value": f"{disc_ratio:.1f}%"},
                    {"metric": "Total Spending", "value": f"${expenses.get('total_expenses', 0.0):,.2f}"},
                ],
            )
        )

    # 4. Emergency fund strength insight
    if runway < Decimal("3.0"):
        insights.append(
            ProactiveInsightSchema(
                id=f"insight-runway-alert-{uuid.uuid4().hex[:8]}",
                insight_type="goal_risk",
                title="Emergency Buffer Below Target",
                description=(
                    f"Your liquid emergency runway is {runway:.1f} months. Building this buffer to at least 3 months "
                    f"protects against unforeseen cash shocks."
                ),
                severity="high",
                action_prompt="How can I optimize my budget to build a 3-month emergency fund?",
                metric_facts=[
                    {"metric": "Current Runway", "value": f"{runway:.1f} months"},
                    {"metric": "Target Runway", "value": "3.0-6.0 months"},
                ],
            )
        )
    elif runway >= Decimal("6.0"):
        insights.append(
            ProactiveInsightSchema(
                id=f"insight-runway-healthy-{uuid.uuid4().hex[:8]}",
                insight_type="rebalancing_opportunity",
                title="Strong Emergency Liquidity Foundation",
                description=(
                    f"You have {runway:.1f} months of emergency savings buffer ($"
                    f"{profile.get('emergency_savings', 0.0):,.2f}). You can safely direct extra monthly surplus toward higher-yield goals."
                ),
                severity="info",
                action_prompt="How should I allocate surplus beyond my emergency fund?",
                metric_facts=[
                    {"metric": "Emergency Runway", "value": f"{runway:.1f} months"},
                    {"metric": "Health Score", "value": f"{health_score:.0f}/100"},
                ],
            )
        )

    return insights
