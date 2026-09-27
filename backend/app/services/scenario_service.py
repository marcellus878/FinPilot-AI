import uuid
from decimal import Decimal
from typing import Any, Dict, List, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.financial_engine.helpers import quantize_currency
from app.financial_engine.scenarios import (
    DetailedScenarioResult,
    FinancialSnapshot,
    FinancialSnapshotDelta,
    GoalScenarioImpact,
    compare_decision_scenarios,
    simulate_detailed_decision_scenario,
)
from app.models.financial_plan import FinancialPlan
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.schemas.scenario import (
    FinancialMetricsDeltaSchema,
    FinancialMetricsSnapshotSchema,
    GoalScenarioImpactSchema,
    ScenarioCompareRequest,
    ScenarioCompareResponse,
    ScenarioSimulateRequest,
    ScenarioSimulateResponse,
    ScenarioTradeoffSummaryItem,
)


def get_user_baseline_financial_state(
    db: Session, user_id: uuid.UUID
) -> Tuple[Decimal, Decimal, Decimal, Decimal, List[Dict[str, Any]]]:
    """Retrieves user's baseline financial variables without modifying anything."""
    # 1. Fetch Profile
    prof_stmt = select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    profile = db.scalar(prof_stmt)

    # Defaults if profile is missing
    income = Decimal("5000.00")
    essential = Decimal("2500.00")
    debt = Decimal("0.00")
    savings = Decimal("10000.00")

    if profile:
        income = profile.monthly_income or Decimal("5000.00")
        essential = profile.essential_expenses or Decimal("2500.00")
        debt = profile.monthly_debt_payment or Decimal("0.00")
        savings = profile.current_savings or Decimal("10000.00")

    # 2. Check active plan for additional recurring income or adjustments
    plan_stmt = select(FinancialPlan).where(FinancialPlan.user_id == user_id, FinancialPlan.is_active == True)
    active_plan = db.scalar(plan_stmt)
    if active_plan and active_plan.plan_data:
        sal_prof = active_plan.plan_data.get("salary_profile", {})
        addl = sal_prof.get("additional_recurring_income")
        if addl:
            income += Decimal(str(addl))

    # 3. Fetch active Goals
    goals_stmt = select(Goal).where(Goal.user_id == user_id, Goal.status != "achieved")
    goals = list(db.scalars(goals_stmt).all())
    active_goals_dicts = [
        {
            "id": str(g.id),
            "name": g.name,
            "target_amount": g.target_amount,
            "current_amount": g.current_amount,
            "monthly_contribution": g.monthly_contribution or Decimal("0.00"),
            "target_date": g.target_date,
        }
        for g in goals
    ]

    return (
        quantize_currency(income),
        quantize_currency(essential),
        quantize_currency(debt),
        quantize_currency(savings),
        active_goals_dicts,
    )


def _map_snapshot_to_schema(snap: FinancialSnapshot) -> FinancialMetricsSnapshotSchema:
    return FinancialMetricsSnapshotSchema(
        monthly_income=str(snap.monthly_income),
        monthly_essential_expenses=str(snap.monthly_essential_expenses),
        monthly_debt_payments=str(snap.monthly_debt_payments),
        monthly_disposable_income=str(snap.monthly_disposable_income),
        current_savings=str(snap.current_savings),
        savings_rate=str(snap.savings_rate),
        debt_to_income_ratio=str(snap.debt_to_income_ratio),
        emergency_fund_months=str(snap.emergency_fund_months),
        emergency_fund_status=snap.emergency_fund_status,
        daily_safe_to_spend=str(snap.daily_safe_to_spend),
        financial_health_score=str(snap.financial_health_score),
        financial_health_grade=snap.financial_health_grade,
    )


def _map_delta_to_schema(delta: FinancialSnapshotDelta) -> FinancialMetricsDeltaSchema:
    return FinancialMetricsDeltaSchema(
        monthly_income_delta=str(delta.monthly_income_delta),
        monthly_essential_expenses_delta=str(delta.monthly_essential_expenses_delta),
        monthly_disposable_income_delta=str(delta.monthly_disposable_income_delta),
        savings_delta=str(delta.savings_delta),
        savings_rate_delta=str(delta.savings_rate_delta),
        debt_to_income_delta=str(delta.debt_to_income_delta),
        emergency_fund_months_delta=str(delta.emergency_fund_months_delta),
        daily_safe_to_spend_delta=str(delta.daily_safe_to_spend_delta),
        financial_health_score_delta=str(delta.financial_health_score_delta),
    )


def _map_goal_impacts_to_schema(impacts: List[GoalScenarioImpact]) -> List[GoalScenarioImpactSchema]:
    return [
        GoalScenarioImpactSchema(
            goal_id=gi.goal_id,
            goal_name=gi.goal_name,
            target_amount=str(gi.target_amount),
            current_amount=str(gi.current_amount),
            previous_monthly_contribution=str(gi.previous_monthly_contribution),
            new_monthly_contribution=str(gi.new_monthly_contribution),
            previous_months_to_complete=gi.previous_months_to_complete,
            new_months_to_complete=gi.new_months_to_complete,
            timeline_delay_months=gi.timeline_delay_months,
            is_still_feasible=gi.is_still_feasible,
            explanation=gi.explanation,
        )
        for gi in impacts
    ]


def _map_detailed_result_to_schema(res: DetailedScenarioResult) -> ScenarioSimulateResponse:
    return ScenarioSimulateResponse(
        scenario_id=res.scenario_id,
        scenario_name=res.scenario_name,
        scenario_type=res.scenario_type,
        amount=str(res.amount),
        timing_months=res.timing_months,
        description=res.description,
        is_sustainable=res.is_sustainable,
        affordability_verdict=res.affordability_verdict,
        before_state=_map_snapshot_to_schema(res.before_state),
        after_state=_map_snapshot_to_schema(res.after_state),
        delta=_map_delta_to_schema(res.delta),
        goal_impacts=_map_goal_impacts_to_schema(res.goal_impacts),
        warnings=res.warnings,
        tradeoffs=res.tradeoffs,
        recommendation=res.recommendation,
    )


def simulate_user_scenario(
    db: Session, user_id: uuid.UUID, request: ScenarioSimulateRequest
) -> ScenarioSimulateResponse:
    from app.agent.decision_agent import execute_decision_pipeline
    from app.schemas.decision import DecisionRequest

    income, essential, debt, savings, active_goals = get_user_baseline_financial_state(db, user_id)

    dec_req = DecisionRequest(
        decision_type=request.scenario_type,  # type: ignore
        amount=request.amount,
        description=request.name or request.description or "Proposed Decision",
        timing_months=request.timing_months,
    )
    context = {
        "profile": {
            "monthly_income": float(income),
            "essential_expenses": float(essential),
            "monthly_debt_payment": float(debt),
            "current_savings": float(savings),
        },
        "goals_portfolio": {
            "goals": active_goals,
        },
    }

    res, dec_result = execute_decision_pipeline(dec_req, context)
    schema_res = _map_detailed_result_to_schema(res)
    schema_res.decision_result = dec_result
    schema_res.ai_explanation = (
        f"**Decision Evaluation ({res.affordability_verdict.upper()}):** {res.recommendation}\n"
        f"Savings impact: {res.delta.savings_delta:+,.2f}, Emergency runway: {res.after_state.emergency_fund_months} mos."
    )
    return schema_res


def compare_user_scenarios(
    db: Session, user_id: uuid.UUID, request: ScenarioCompareRequest
) -> ScenarioCompareResponse:
    income, essential, debt, savings, active_goals = get_user_baseline_financial_state(db, user_id)

    scenarios_dicts = [
        {
            "id": sc.id or f"scenario_{i+1}",
            "name": sc.name,
            "type": sc.type,
            "amount": sc.amount,
            "timing_months": sc.timing_months,
            "description": sc.description,
        }
        for i, sc in enumerate(request.scenarios[:3])
    ]

    comp_res = compare_decision_scenarios(
        monthly_income=income,
        monthly_essential_expenses=essential,
        monthly_debt_payments=debt,
        current_savings=savings,
        scenarios_list=scenarios_dicts,
        active_goals=active_goals,
    )

    scenarios_schema = [_map_detailed_result_to_schema(s) for s in comp_res.scenarios]
    tradeoffs_schema = [
        ScenarioTradeoffSummaryItem(
            scenario_id=t["scenario_id"],
            scenario_name=t["scenario_name"],
            verdict=t["verdict"],
            ending_savings=t["ending_savings"],
            monthly_cash_flow=t["monthly_cash_flow"],
            emergency_runway_months=t["emergency_runway_months"],
            health_score=t["health_score"],
            health_score_change=t["health_score_change"],
            key_tradeoffs=t["key_tradeoffs"],
            recommendation=t["recommendation"],
        )
        for t in comp_res.tradeoff_summary
    ]

    return ScenarioCompareResponse(
        baseline=_map_snapshot_to_schema(comp_res.baseline),
        scenarios=scenarios_schema,
        tradeoff_summary=tradeoffs_schema,
    )
