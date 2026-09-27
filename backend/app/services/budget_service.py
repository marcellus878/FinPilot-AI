from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.financial_engine import calculate_budget_performance
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.budget import (
    BudgetCreate,
    BudgetPerformanceResponse,
    BudgetResponse,
    BudgetUpdate,
    CategoryBudgetStatusResponse,
)


def create_or_update_budget(
    db: Session,
    user_id: UUID,
    budget_in: BudgetCreate,
) -> Budget:
    cat = budget_in.category.strip()
    period = budget_in.period.strip() if budget_in.period else "monthly"

    existing = (
        db.query(Budget)
        .filter(
            Budget.user_id == user_id,
            Budget.category.ilike(cat),
            Budget.period == period,
        )
        .first()
    )

    if existing:
        existing.monthly_limit = budget_in.monthly_limit
        existing.category = cat
        db.commit()
        db.refresh(existing)
        return existing

    budget = Budget(
        user_id=user_id,
        category=cat,
        monthly_limit=budget_in.monthly_limit,
        period=period,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def get_budget(
    db: Session,
    user_id: UUID,
    budget_id: UUID,
) -> Optional[Budget]:
    return (
        db.query(Budget)
        .filter(Budget.id == budget_id, Budget.user_id == user_id)
        .first()
    )


def list_budgets(
    db: Session,
    user_id: UUID,
    period: Optional[str] = None,
) -> List[Budget]:
    query = db.query(Budget).filter(Budget.user_id == user_id)
    if period:
        query = query.filter(Budget.period == period)
    return query.order_by(Budget.category).all()


def update_budget(
    db: Session,
    user_id: UUID,
    budget_id: UUID,
    budget_in: BudgetUpdate,
) -> Optional[Budget]:
    budget = get_budget(db, user_id, budget_id)
    if not budget:
        return None

    data = budget_in.model_dump(exclude_unset=True)
    for key, val in data.items():
        if val is not None:
            if key == "category":
                setattr(budget, key, str(val).strip())
            else:
                setattr(budget, key, val)

    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(
    db: Session,
    user_id: UUID,
    budget_id: UUID,
) -> bool:
    budget = get_budget(db, user_id, budget_id)
    if not budget:
        return False
    db.delete(budget)
    db.commit()
    return True


def get_user_budget_performance(
    db: Session,
    user_id: UUID,
    period: str = "monthly",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> BudgetPerformanceResponse:
    budgets = list_budgets(db, user_id, period=period)

    # Current month transaction window
    now = datetime.now()
    if not start_date:
        start_date = datetime(now.year, now.month, 1)
    if not end_date:
        end_date = now

    txs = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .all()
    )

    perf = calculate_budget_performance(budgets=budgets, transactions=txs)

    cat_statuses = [
        CategoryBudgetStatusResponse(
            category=c.category,
            monthly_limit=c.monthly_limit,
            actual_spent=c.actual_spent,
            remaining_amount=c.remaining_amount,
            percentage_consumed=c.percentage_consumed,
            variance=c.variance,
            is_over_budget=c.is_over_budget,
            status=c.status,
        )
        for c in perf.category_statuses
    ]

    return BudgetPerformanceResponse(
        total_budgeted=perf.total_budgeted,
        total_spent=perf.total_spent,
        total_remaining=perf.total_remaining,
        overall_percentage_consumed=perf.overall_percentage_consumed,
        overall_variance=perf.overall_variance,
        over_budget_count=perf.over_budget_count,
        category_statuses=cat_statuses,
    )
