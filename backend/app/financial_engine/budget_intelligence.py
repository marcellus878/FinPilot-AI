from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.financial_engine.constants import (
    DECIMAL_ONE_HUNDRED,
    DECIMAL_ZERO,
)
from app.financial_engine.helpers import (
    quantize_currency,
    quantize_percentage,
    to_decimal,
)


@dataclass(frozen=True)
class CategoryBudgetStatusItem:
    category: str
    monthly_limit: Decimal
    actual_spent: Decimal
    remaining_amount: Decimal
    percentage_consumed: Decimal
    variance: Decimal  # actual - limit
    is_over_budget: bool
    status: str  # "under_budget", "on_track", "warning", "over_budget"


@dataclass(frozen=True)
class BudgetPerformanceResult:
    total_budgeted: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    overall_percentage_consumed: Decimal
    overall_variance: Decimal
    over_budget_count: int
    category_statuses: List[CategoryBudgetStatusItem]


def calculate_budget_performance(
    budgets: List[Any],
    transactions: List[Any],
) -> BudgetPerformanceResult:
    category_spending: Dict[str, Decimal] = {}
    for tx in transactions:
        tx_type = getattr(tx, "type", None) or (tx.get("type") if isinstance(tx, dict) else "expense")
        if str(tx_type).lower() != "expense":
            continue

        raw_amt = getattr(tx, "amount", None) if hasattr(tx, "amount") else tx.get("amount")
        amt = quantize_currency(to_decimal(raw_amt, allow_negative=False))
        raw_cat = getattr(tx, "category", None) if hasattr(tx, "category") else tx.get("category")
        cat_key = str(raw_cat or "Uncategorized").strip().lower()

        category_spending[cat_key] = category_spending.get(cat_key, DECIMAL_ZERO) + amt

    category_statuses: List[CategoryBudgetStatusItem] = []
    total_budgeted = DECIMAL_ZERO
    total_spent_budgeted_categories = DECIMAL_ZERO
    over_budget_count = 0

    for b in budgets:
        raw_cat = getattr(b, "category", None) if hasattr(b, "category") else b.get("category")
        cat_display = str(raw_cat or "General").strip()
        cat_key = cat_display.lower()

        raw_lim = getattr(b, "monthly_limit", None) if hasattr(b, "monthly_limit") else b.get("monthly_limit")
        limit = quantize_currency(to_decimal(raw_lim, allow_negative=False))

        spent = category_spending.get(cat_key, DECIMAL_ZERO)
        total_budgeted += limit
        total_spent_budgeted_categories += spent

        remaining = quantize_currency(max(DECIMAL_ZERO, limit - spent))
        variance = quantize_currency(spent - limit)
        is_over = spent > limit

        if limit > DECIMAL_ZERO:
            pct_consumed = quantize_percentage((spent / limit) * DECIMAL_ONE_HUNDRED)
        else:
            pct_consumed = DECIMAL_ONE_HUNDRED if spent > DECIMAL_ZERO else DECIMAL_ZERO

        if is_over:
            status = "over_budget"
            over_budget_count += 1
        elif pct_consumed >= Decimal("85.00"):
            status = "warning"
        elif pct_consumed >= Decimal("50.00"):
            status = "on_track"
        else:
            status = "under_budget"

        category_statuses.append(
            CategoryBudgetStatusItem(
                category=cat_display,
                monthly_limit=limit,
                actual_spent=spent,
                remaining_amount=remaining,
                percentage_consumed=pct_consumed,
                variance=variance,
                is_over_budget=is_over,
                status=status,
            )
        )

    total_remaining = quantize_currency(max(DECIMAL_ZERO, total_budgeted - total_spent_budgeted_categories))
    overall_variance = quantize_currency(total_spent_budgeted_categories - total_budgeted)
    overall_pct = (
        quantize_percentage((total_spent_budgeted_categories / total_budgeted) * DECIMAL_ONE_HUNDRED)
        if total_budgeted > DECIMAL_ZERO
        else DECIMAL_ZERO
    )

    return BudgetPerformanceResult(
        total_budgeted=total_budgeted,
        total_spent=total_spent_budgeted_categories,
        total_remaining=total_remaining,
        overall_percentage_consumed=overall_pct,
        overall_variance=overall_variance,
        over_budget_count=over_budget_count,
        category_statuses=category_statuses,
    )
