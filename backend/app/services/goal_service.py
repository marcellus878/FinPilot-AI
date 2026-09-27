import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.financial_engine.goals import (
    analyze_goal_portfolio,
    generate_goal_conflict_strategies,
)
from app.financial_engine.helpers import quantize_currency, to_decimal
from app.models.financial_plan import FinancialPlan
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.schemas.goal import (
    GoalAnalysisItem,
    GoalAnalysisResponse,
    GoalConflictAllocationItem,
    GoalConflictResponse,
    GoalConflictStrategySchema,
    GoalCreate,
    GoalUpdate,
)


def get_goals(db: Session, user_id: uuid.UUID) -> List[Goal]:
    statement = select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at.desc())
    return list(db.scalars(statement).all())


def get_goal_by_id(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> Optional[Goal]:
    statement = select(Goal).where(Goal.id == goal_id, Goal.user_id == user_id)
    return db.scalar(statement)


def create_goal(db: Session, user_id: uuid.UUID, goal_in: GoalCreate) -> Goal:
    goal = Goal(
        user_id=user_id,
        name=goal_in.name,
        target_amount=quantize_currency(goal_in.target_amount),
        current_amount=quantize_currency(goal_in.current_amount),
        target_date=goal_in.target_date,
        priority=goal_in.priority.lower(),
        category=goal_in.category,
        monthly_contribution=quantize_currency(goal_in.monthly_contribution) if goal_in.monthly_contribution is not None else None,
        status=goal_in.status.lower(),
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID, goal_in: GoalUpdate) -> Optional[Goal]:
    goal = get_goal_by_id(db, user_id, goal_id)
    if not goal:
        return None

    update_data = goal_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("target_amount", "current_amount", "monthly_contribution") and value is not None:
            setattr(goal, field, quantize_currency(value))
        elif field in ("priority", "status") and value is not None:
            setattr(goal, field, value.lower())
        else:
            setattr(goal, field, value)

    # Auto-update status to achieved if current >= target
    if goal.current_amount >= goal.target_amount and goal.target_amount > 0:
        goal.status = "achieved"

    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> bool:
    goal = get_goal_by_id(db, user_id, goal_id)
    if not goal:
        return False
    db.delete(goal)
    db.commit()
    return True


def get_available_goal_capacity(db: Session, user_id: uuid.UUID) -> Decimal:
    """Computes available monthly savings/goal funding capacity from user financial state."""
    # 1. Check active FinancialPlan plan_data
    plan_stmt = select(FinancialPlan).where(FinancialPlan.user_id == user_id, FinancialPlan.is_active == True)
    active_plan = db.scalar(plan_stmt)
    if active_plan and active_plan.plan_data:
        alloc = active_plan.plan_data.get("allocation", {})
        savings_target = alloc.get("savings_target")
        remaining_buffer = alloc.get("remaining_buffer")
        if savings_target is not None:
            tot = to_decimal(savings_target) + max(Decimal("0.00"), to_decimal(remaining_buffer or 0))
            if tot > 0:
                return quantize_currency(tot)

    # 2. Check FinancialProfile
    prof_stmt = select(FinancialProfile).where(FinancialProfile.user_id == user_id)
    profile = db.scalar(prof_stmt)
    if profile:
        monthly_income = profile.monthly_income or Decimal("0.00")
        essential_expenses = profile.essential_expenses or Decimal("0.00")
        debt_payment = profile.monthly_debt_payment or Decimal("0.00")
        disposable = max(Decimal("0.00"), monthly_income - essential_expenses - debt_payment)
        return quantize_currency(disposable)

    return Decimal("1000.00")  # sensible baseline default


def analyze_user_goals(db: Session, user_id: uuid.UUID) -> GoalAnalysisResponse:
    goals = get_goals(db, user_id)
    capacity = get_available_goal_capacity(db, user_id)

    goals_dicts = [
        {
            "id": str(g.id),
            "name": g.name,
            "category": g.category or "General",
            "priority": g.priority or "medium",
            "status": g.status or "in_progress",
            "target_amount": g.target_amount,
            "current_amount": g.current_amount,
            "target_date": g.target_date,
            "monthly_contribution": g.monthly_contribution,
        }
        for g in goals
    ]

    analysis = analyze_goal_portfolio(goals_dicts, capacity)

    evaluations_schema = [
        GoalAnalysisItem(
            id=ev["id"],
            name=ev["name"],
            category=ev["category"],
            priority=ev["priority"],
            status=ev["status"],
            target_amount=str(ev["target_amount"]),
            current_amount=str(ev["current_amount"]),
            remaining_amount=str(ev["remaining_amount"]),
            progress_percentage=str(ev["progress_percentage"]),
            target_date=ev["target_date"],
            monthly_contribution=ev["monthly_contribution"],
            required_monthly_contribution=str(ev["required_monthly_contribution"]),
            months_remaining_deadline=ev["months_remaining_deadline"],
            months_to_projected_completion=ev["months_to_projected_completion"],
            projected_completion_date=ev["projected_completion_date"],
            is_feasible=ev["is_feasible"],
            is_completed=ev["is_completed"],
            feasibility_explanation=ev["feasibility_explanation"],
            shortfall_or_surplus=str(ev["shortfall_or_surplus"]),
        )
        for ev in analysis.goal_evaluations
    ]

    strategies_schema = [
        GoalConflictStrategySchema(
            strategy_id=st.strategy_id,
            strategy_name=st.strategy_name,
            description=st.description,
            total_allocated=str(st.total_allocated),
            remaining_unallocated=str(st.remaining_unallocated),
            fully_funded_count=st.fully_funded_count,
            unfunded_count=st.unfunded_count,
            allocations=[
                GoalConflictAllocationItem(
                    goal_id=al.goal_id,
                    goal_name=al.goal_name,
                    priority=al.priority,
                    target_amount=str(al.target_amount),
                    current_amount=str(al.current_amount),
                    monthly_target_contribution=str(al.monthly_target_contribution),
                    allocated_amount=str(al.allocated_amount),
                    is_fully_funded=al.is_fully_funded,
                    shortfall=str(al.shortfall),
                )
                for al in st.allocations
            ],
        )
        for st in analysis.conflict_alternatives
    ]

    return GoalAnalysisResponse(
        total_target_amount=str(analysis.total_target_amount),
        total_saved_amount=str(analysis.total_saved_amount),
        total_remaining_amount=str(analysis.total_remaining_amount),
        overall_progress_percentage=str(analysis.overall_progress_percentage),
        total_required_monthly=str(analysis.total_required_monthly),
        available_monthly_capacity=str(analysis.available_monthly_capacity),
        net_monthly_surplus_or_shortfall=str(analysis.net_monthly_surplus_or_shortfall),
        is_portfolio_feasible=analysis.is_portfolio_feasible,
        conflict_detected=analysis.conflict_detected,
        active_goals_count=analysis.active_goals_count,
        achieved_goals_count=analysis.achieved_goals_count,
        goal_evaluations=evaluations_schema,
        conflict_alternatives=strategies_schema,
        summary_explanation=analysis.summary_explanation,
    )


def get_user_goal_conflicts(db: Session, user_id: uuid.UUID) -> GoalConflictResponse:
    analysis = analyze_user_goals(db, user_id)
    active_goals = [g for g in analysis.goal_evaluations if not g.is_completed]

    if analysis.conflict_detected:
        explanation = (
            f"Conflict Detected: Your active goals require ${analysis.total_required_monthly}/month, "
            f"which exceeds your available capacity (${analysis.available_monthly_capacity}) "
            f"by ${abs(Decimal(analysis.net_monthly_surplus_or_shortfall))}."
        )
    else:
        explanation = "No goal conflicts detected. Available monthly capacity comfortably supports active goals."

    return GoalConflictResponse(
        conflict_detected=analysis.conflict_detected,
        total_available_capacity=analysis.available_monthly_capacity,
        total_required_monthly=analysis.total_required_monthly,
        shortfall=str(max(Decimal("0.00"), Decimal(analysis.total_required_monthly) - Decimal(analysis.available_monthly_capacity))),
        active_goals_count=len(active_goals),
        goals_involved=active_goals,
        strategies=analysis.conflict_alternatives,
        explanation=explanation,
    )
