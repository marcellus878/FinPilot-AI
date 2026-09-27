from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.financial_engine.budget_intelligence import calculate_budget_performance
from app.financial_engine.core_metrics import (
    calculate_debt_to_income_ratio,
    calculate_disposable_income,
    calculate_emergency_fund_status,
    calculate_expense_ratio,
    calculate_savings_rate,
)
from app.financial_engine.expense_intelligence import (
    calculate_category_breakdown,
    calculate_expense_summary,
    detect_unusual_spending,
)
from app.financial_engine.goals import analyze_goal_portfolio
from app.financial_engine.health_score import calculate_financial_health_score
from app.financial_engine.helpers import quantize_currency, safe_divide
from app.financial_engine.salary_planner import (
    calculate_monthly_recurring_commitments,
    calculate_safe_to_spend,
    calculate_salary_allocation,
    calculate_salary_cycle_dates,
    calculate_survival_projection,
)
from app.financial_engine.spending_intelligence import calculate_spending_intelligence
from app.models.budget import Budget
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.models.user import User


def build_financial_context(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
    """
    Assembles a complete, deterministic financial fact context for a user.
    Agents rely strictly on these pre-computed numbers without calculating raw finances themselves.
    """
    user = db.scalar(select(User).where(User.id == user_id))
    profile = db.scalar(select(FinancialProfile).where(FinancialProfile.user_id == user_id))
    
    # 1. Base Profile
    monthly_income = float(profile.monthly_income) if profile else 0.0
    current_savings = float(profile.current_savings) if profile else 0.0
    monthly_debt = float(profile.monthly_debt_payment) if profile else 0.0
    essential_expenses = float(profile.essential_expenses) if profile else 0.0
    emergency_savings = float(profile.emergency_savings) if profile else 0.0
    dependents = profile.dependents if profile else 0
    risk_preference = profile.risk_preference if profile else "moderate"

    # 2. Query Transactions
    transactions_query = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc())
    )
    db_transactions = list(db.scalars(transactions_query).all())
    
    tx_dicts = [
        {
            "id": str(t.id),
            "amount": float(t.amount),
            "type": t.type,
            "category": t.category,
            "description": t.description,
            "transaction_date": t.transaction_date.isoformat() if t.transaction_date else None,
        }
        for t in db_transactions
    ]

    # 3. Query Budgets
    budgets_query = select(Budget).where(Budget.user_id == user_id)
    db_budgets = list(db.scalars(budgets_query).all())
    budget_dicts = [
        {
            "id": str(b.id),
            "category": b.category,
            "monthly_limit": float(b.monthly_limit),
            "period": b.period,
        }
        for b in db_budgets
    ]

    # 4. Query Goals
    goals_query = select(Goal).where(Goal.user_id == user_id)
    db_goals = list(db.scalars(goals_query).all())
    goal_dicts = [
        {
            "id": str(g.id),
            "name": g.name,
            "target_amount": float(g.target_amount),
            "current_amount": float(g.current_amount),
            "target_date": g.target_date.isoformat() if g.target_date else None,
            "priority": g.priority,
            "monthly_contribution": float(g.monthly_contribution) if g.monthly_contribution else 0.0,
            "status": g.status,
        }
        for g in db_goals
    ]

    # 5. Deterministic Core Calculations
    disposable_income = float(calculate_disposable_income(monthly_income, essential_expenses, monthly_debt))
    savings_rate = float(calculate_savings_rate(disposable_income, monthly_income)) if monthly_income > 0 else 0.0
    expense_ratio = float(calculate_expense_ratio(essential_expenses + monthly_debt, monthly_income)) if monthly_income > 0 else 0.0
    dti_ratio = float(calculate_debt_to_income_ratio(monthly_debt, monthly_income)) if monthly_income > 0 else 0.0
    emergency_status = calculate_emergency_fund_status(emergency_savings, essential_expenses)

    # 6. Expense & Spending Intelligence
    expense_summary = calculate_expense_summary(tx_dicts)
    category_breakdown = calculate_category_breakdown(tx_dicts)
    unusual_flags = detect_unusual_spending(tx_dicts)
    spending_intel = calculate_spending_intelligence(tx_dicts)

    # 7. Budget Performance
    budget_performance = calculate_budget_performance(budget_dicts, tx_dicts)

    # 8. Salary & Cash Flow
    now = datetime.now()
    salary_cycle = calculate_salary_cycle_dates(expected_salary_day=1, reference_date=now)
    _, total_recurring_commitments, upcoming_commitments = calculate_monthly_recurring_commitments(
        commitments=tx_dicts,
        next_salary_date=salary_cycle.next_salary_date,
        reference_date=now,
    )
    salary_allocation = calculate_salary_allocation(
        monthly_income=Decimal(str(monthly_income)),
        fixed_commitments=total_recurring_commitments,
    )
    safe_to_spend = calculate_safe_to_spend(
        current_available_funds=Decimal(str(current_savings)),
        upcoming_commitments=upcoming_commitments,
        remaining_essential_allowance=Decimal(str(essential_expenses)),
        savings_reserve=salary_allocation.savings_target,
        emergency_reserve=Decimal(str(emergency_savings)),
        days_remaining=salary_cycle.days_remaining,
    )
    daily_burn = (Decimal(str(expense_summary.total_expenses)) / Decimal("30.00")) if expense_summary.total_expenses > 0 else Decimal("0.00")
    survival_projection = calculate_survival_projection(
        current_available_funds=Decimal(str(current_savings)),
        monthly_income=Decimal(str(monthly_income)),
        recent_average_daily_burn=daily_burn,
        days_remaining=salary_cycle.days_remaining,
        upcoming_commitments=upcoming_commitments,
        remaining_essential_allowance=Decimal(str(essential_expenses)),
    )

    # 9. Goals Portfolio
    goals_portfolio = analyze_goal_portfolio(goal_dicts, available_monthly_capacity=Decimal(str(disposable_income)))

    # 10. Financial Health Score
    health_score_res = calculate_financial_health_score(
        monthly_income=Decimal(str(monthly_income)),
        essential_expenses=Decimal(str(essential_expenses)),
        monthly_debt_payments=Decimal(str(monthly_debt)),
        current_savings=Decimal(str(current_savings)),
        budget_discipline_pct=Decimal(str(100.0 - min(100.0, float(budget_performance.overall_percentage_consumed)))),
        goal_progress_pct=Decimal(str(goals_portfolio.overall_progress_percentage)),
    )

    return {
        "user": {
            "id": str(user.id) if user else str(user_id),
            "email": user.email if user else "",
            "full_name": user.full_name if user else "",
        },
        "profile": {
            "monthly_income": monthly_income,
            "current_savings": current_savings,
            "monthly_debt_payment": monthly_debt,
            "essential_expenses": essential_expenses,
            "emergency_savings": emergency_savings,
            "dependents": dependents,
            "risk_preference": risk_preference,
        },
        "core_metrics": {
            "disposable_income": disposable_income,
            "savings_rate": savings_rate,
            "expense_ratio": expense_ratio,
            "debt_to_income_ratio": dti_ratio,
            "emergency_fund_months": float(emergency_status.months_covered),
            "emergency_fund_target": float(emergency_status.target_amount),
            "emergency_fund_shortfall": float(emergency_status.shortfall),
            "emergency_fund_status": emergency_status.status_label,
            "is_emergency_fund_adequate": emergency_status.is_adequate,
        },
        "expense_summary": {
            "total_expenses": float(expense_summary.total_expenses),
            "essential_expenses": float(expense_summary.essential_spending),
            "discretionary_expenses": float(expense_summary.non_essential_spending),
            "essential_ratio": float(expense_summary.essential_percentage),
            "discretionary_ratio": float(expense_summary.non_essential_percentage),
            "transaction_count": expense_summary.transaction_count,
        },
        "category_spending": [
            {
                "category": cat.category,
                "total_amount": float(cat.total_amount),
                "percentage_of_total": float(cat.percentage_of_total),
                "transaction_count": cat.transaction_count,
                "is_essential": cat.is_essential,
            }
            for cat in category_breakdown
        ],
        "unusual_spending_flags": [
            {
                "category": f.category,
                "current_month_amount": float(f.current_month_amount),
                "baseline_average": float(f.baseline_average),
                "percentage_change": float(f.percentage_change),
                "flag_reason": f.flag_reason,
            }
            for f in unusual_flags
        ],
        "spending_intelligence": {
            "recurring_expenses": [
                {
                    "merchant": r.merchant,
                    "category": r.category,
                    "estimated_amount": float(r.approximate_amount),
                    "frequency": r.frequency,
                    "occurrence_count": r.occurrence_count,
                }
                for r in spending_intel.recurring_expenses
            ],
            "spending_habits": [
                {
                    "habit_title": h.habit_name,
                    "category": h.category,
                    "description": h.description,
                    "frequency": h.frequency_per_month,
                    "avg_transaction_amount": float(h.monthly_cost) / max(1, h.frequency_per_month),
                    "estimated_monthly_impact": float(h.monthly_cost),
                }
                for h in spending_intel.habits
            ],
            "miscellaneous_spending": {
                "total_miscellaneous_amount": float(spending_intel.miscellaneous_analysis.total_miscellaneous_amount),
                "percentage_of_total_spend": float(spending_intel.miscellaneous_analysis.percentage_of_expenses),
                "leak_risk_level": spending_intel.miscellaneous_analysis.leak_severity,
                "actionable_recommendation": spending_intel.miscellaneous_analysis.description,
            },
            "hidden_expenses": [
                {
                    "name": he.merchant,
                    "category": he.category,
                    "monthly_leak": float(he.total_monthly_cost),
                    "annual_leak": float(he.annualized_cost),
                    "optimization_tip": he.description,
                }
                for he in spending_intel.hidden_expenses
            ],
        },
        "budget_performance": {
            "total_budgeted": float(budget_performance.total_budgeted),
            "total_actual": float(budget_performance.total_spent),
            "overall_utilization_percentage": float(budget_performance.overall_percentage_consumed),
            "categories": [
                {
                    "category": cat_b.category,
                    "budgeted": float(cat_b.monthly_limit),
                    "actual": float(cat_b.actual_spent),
                    "utilization_percentage": float(cat_b.percentage_consumed),
                    "status": cat_b.status,
                    "is_over_budget": cat_b.is_over_budget,
                }
                for cat_b in budget_performance.category_statuses
            ],
        },
        "cash_flow": {
            "days_until_payday": salary_cycle.days_remaining,
            "safe_to_spend_daily": float(safe_to_spend.daily_safe_to_spend),
            "safe_to_spend_weekly": float(safe_to_spend.daily_safe_to_spend * Decimal("7.00")),
            "safe_to_spend_remaining_cycle": float(safe_to_spend.safe_to_spend_amount),
            "status": survival_projection.status,
            "survival_months_strict_essentials": float(emergency_status.months_covered),
            "survival_months_current_lifestyle": float(safe_divide(Decimal(str(current_savings)), expense_summary.total_expenses)) if expense_summary.total_expenses > 0 else 999.0,
        },
        "goals_portfolio": {
            "total_goals_count": goals_portfolio.active_goals_count + goals_portfolio.achieved_goals_count,
            "active_goals_count": goals_portfolio.active_goals_count,
            "total_target_amount": float(goals_portfolio.total_target_amount),
            "total_saved_amount": float(goals_portfolio.total_saved_amount),
            "total_monthly_required": float(goals_portfolio.total_required_monthly),
            "has_conflicts": goals_portfolio.conflict_detected,
            "conflict_shortfall": float(abs(goals_portfolio.net_monthly_surplus_or_shortfall)) if goals_portfolio.conflict_detected else 0.0,
            "goals": [
                {
                    "name": g["name"],
                    "target_amount": float(g["target_amount"]),
                    "current_amount": float(g["current_amount"]),
                    "monthly_contribution": float(g["monthly_contribution"]) if g.get("monthly_contribution") else 0.0,
                    "required_monthly": float(g["required_monthly_contribution"]),
                    "is_on_track": g["is_feasible"],
                }
                for g in goals_portfolio.goal_evaluations
            ],
        },
        "financial_health_score": {
            "overall_score": float(health_score_res.overall_score),
            "status": health_score_res.grade,
            "summary": f"Health Score: {health_score_res.overall_score}/100 ({health_score_res.grade})",
            "savings_score": float(health_score_res.component_scores.get("savings_rate", 0.0)),
            "emergency_score": float(health_score_res.component_scores.get("emergency_fund", 0.0)),
            "debt_score": float(health_score_res.component_scores.get("debt_to_income", 0.0)),
            "budget_score": float(health_score_res.component_scores.get("budget_discipline", 0.0)),
            "discretionary_score": float(health_score_res.component_scores.get("goal_progress", 0.0)),
        },
    }
