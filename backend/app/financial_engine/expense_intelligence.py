from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from app.financial_engine.constants import (
    DECIMAL_ONE_HUNDRED,
    DECIMAL_ZERO,
)
from app.financial_engine.helpers import (
    quantize_currency,
    quantize_percentage,
    safe_divide,
    to_decimal,
)

DEFAULT_ESSENTIAL_CATEGORIES = {
    "housing",
    "rent",
    "mortgage",
    "utilities",
    "groceries",
    "transportation",
    "healthcare",
    "insurance",
    "debt",
    "loan",
    "medical",
    "bills",
    "education",
}


@dataclass(frozen=True)
class CategorySpendingItem:
    category: str
    total_amount: Decimal
    percentage_of_total: Decimal
    transaction_count: int
    is_essential: bool


@dataclass(frozen=True)
class SpendingFlagItem:
    flag_type: str  # "high_transaction", "over_budget", "unusual_category_spend"
    severity: str  # "warning", "critical", "info"
    category: str
    description: str
    amount: Decimal
    threshold: Decimal


@dataclass(frozen=True)
class MonthOverMonthResult:
    previous_total_expenses: Decimal
    current_total_expenses: Decimal
    delta_amount: Decimal
    delta_percentage: Decimal
    trend: str  # "increased", "decreased", "stable"


@dataclass(frozen=True)
class ExpenseSummaryResult:
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    savings_rate: Decimal
    essential_spending: Decimal
    non_essential_spending: Decimal
    essential_percentage: Decimal
    non_essential_percentage: Decimal
    transaction_count: int
    income_transaction_count: int
    expense_transaction_count: int
    month_over_month: Optional[MonthOverMonthResult]
    category_breakdown: List[CategorySpendingItem]
    largest_categories: List[CategorySpendingItem]
    spending_flags: List[SpendingFlagItem]


def is_category_essential(category: str) -> bool:
    norm = category.strip().lower()
    return any(ess in norm for ess in DEFAULT_ESSENTIAL_CATEGORIES)


def calculate_category_breakdown(transactions: List[Any]) -> List[CategorySpendingItem]:
    category_totals: Dict[str, Decimal] = {}
    category_counts: Dict[str, int] = {}
    total_expenses = DECIMAL_ZERO

    for tx in transactions:
        tx_type = getattr(tx, "type", None) or (tx.get("type") if isinstance(tx, dict) else "expense")
        if str(tx_type).lower() != "expense":
            continue

        raw_amt = getattr(tx, "amount", None) if hasattr(tx, "amount") else tx.get("amount")
        amt = quantize_currency(to_decimal(raw_amt, allow_negative=False, name="transaction_amount"))

        raw_cat = getattr(tx, "category", None) if hasattr(tx, "category") else tx.get("category")
        cat = str(raw_cat or "Uncategorized").strip()

        category_totals[cat] = category_totals.get(cat, DECIMAL_ZERO) + amt
        category_counts[cat] = category_counts.get(cat, 0) + 1
        total_expenses += amt

    items: List[CategorySpendingItem] = []
    for cat, cat_amt in category_totals.items():
        pct = (
            quantize_percentage((cat_amt / total_expenses) * DECIMAL_ONE_HUNDRED)
            if total_expenses > DECIMAL_ZERO
            else DECIMAL_ZERO
        )
        items.append(
            CategorySpendingItem(
                category=cat,
                total_amount=cat_amt,
                percentage_of_total=pct,
                transaction_count=category_counts[cat],
                is_essential=is_category_essential(cat),
            )
        )

    items.sort(key=lambda x: x.total_amount, reverse=True)
    return items


def detect_unusual_spending(
    transactions: List[Any],
    budgets: Optional[List[Any]] = None,
) -> List[SpendingFlagItem]:
    flags: List[SpendingFlagItem] = []
    budget_map: Dict[str, Decimal] = {}

    if budgets:
        for b in budgets:
            b_cat = getattr(b, "category", None) if hasattr(b, "category") else b.get("category")
            b_lim = getattr(b, "monthly_limit", None) if hasattr(b, "monthly_limit") else b.get("monthly_limit")
            if b_cat:
                budget_map[str(b_cat).strip().lower()] = to_decimal(b_lim, allow_negative=False)

    for tx in transactions:
        tx_type = getattr(tx, "type", None) or (tx.get("type") if isinstance(tx, dict) else "expense")
        if str(tx_type).lower() != "expense":
            continue

        raw_amt = getattr(tx, "amount", None) if hasattr(tx, "amount") else tx.get("amount")
        amt = quantize_currency(to_decimal(raw_amt, allow_negative=False))
        raw_cat = getattr(tx, "category", None) if hasattr(tx, "category") else tx.get("category")
        cat = str(raw_cat or "Uncategorized").strip()
        cat_lower = cat.lower()

        # Check if single transaction > 50% of monthly category budget
        if cat_lower in budget_map and budget_map[cat_lower] > DECIMAL_ZERO:
            b_limit = budget_map[cat_lower]
            threshold = quantize_currency(b_limit * Decimal("0.50"))
            if amt >= threshold:
                desc = getattr(tx, "description", None) or (tx.get("description") if isinstance(tx, dict) else "")
                flags.append(
                    SpendingFlagItem(
                        flag_type="high_transaction",
                        severity="warning",
                        category=cat,
                        description=f"Single purchase of ${amt} exceeds 50% of the monthly ${b_limit} budget ({desc or cat}).",
                        amount=amt,
                        threshold=threshold,
                    )
                )

    return flags


def calculate_expense_summary(
    transactions: List[Any],
    previous_period_transactions: Optional[List[Any]] = None,
    budgets: Optional[List[Any]] = None,
) -> ExpenseSummaryResult:
    total_income = DECIMAL_ZERO
    total_expenses = DECIMAL_ZERO
    essential_spending = DECIMAL_ZERO
    non_essential_spending = DECIMAL_ZERO
    income_count = 0
    expense_count = 0

    for tx in transactions:
        tx_type = getattr(tx, "type", None) or (tx.get("type") if isinstance(tx, dict) else "expense")
        raw_amt = getattr(tx, "amount", None) if hasattr(tx, "amount") else tx.get("amount")
        amt = quantize_currency(to_decimal(raw_amt, allow_negative=False))
        raw_cat = getattr(tx, "category", None) if hasattr(tx, "category") else tx.get("category")
        cat = str(raw_cat or "Uncategorized").strip()

        if str(tx_type).lower() == "income":
            total_income += amt
            income_count += 1
        else:
            total_expenses += amt
            expense_count += 1
            if is_category_essential(cat):
                essential_spending += amt
            else:
                non_essential_spending += amt

    net_savings = quantize_currency(total_income - total_expenses)
    savings_rate = (
        quantize_percentage((net_savings / total_income) * DECIMAL_ONE_HUNDRED)
        if total_income > DECIMAL_ZERO
        else DECIMAL_ZERO
    )

    essential_pct = (
        quantize_percentage((essential_spending / total_expenses) * DECIMAL_ONE_HUNDRED)
        if total_expenses > DECIMAL_ZERO
        else DECIMAL_ZERO
    )
    non_essential_pct = (
        quantize_percentage((non_essential_spending / total_expenses) * DECIMAL_ONE_HUNDRED)
        if total_expenses > DECIMAL_ZERO
        else DECIMAL_ZERO
    )

    # Month over month
    mom_result: Optional[MonthOverMonthResult] = None
    if previous_period_transactions is not None and len(previous_period_transactions) > 0:
        prev_expenses = DECIMAL_ZERO
        for tx in previous_period_transactions:
            tx_type = getattr(tx, "type", None) or (tx.get("type") if isinstance(tx, dict) else "expense")
            if str(tx_type).lower() == "expense":
                raw_amt = getattr(tx, "amount", None) if hasattr(tx, "amount") else tx.get("amount")
                prev_expenses += quantize_currency(to_decimal(raw_amt, allow_negative=False))

        delta_amt = quantize_currency(total_expenses - prev_expenses)
        delta_pct = (
            quantize_percentage((delta_amt / prev_expenses) * DECIMAL_ONE_HUNDRED)
            if prev_expenses > DECIMAL_ZERO
            else DECIMAL_ZERO
        )
        if delta_amt > Decimal("10.00"):
            trend = "increased"
        elif delta_amt < Decimal("-10.00"):
            trend = "decreased"
        else:
            trend = "stable"

        mom_result = MonthOverMonthResult(
            previous_total_expenses=prev_expenses,
            current_total_expenses=total_expenses,
            delta_amount=delta_amt,
            delta_percentage=delta_pct,
            trend=trend,
        )

    categories = calculate_category_breakdown(transactions)
    largest = categories[:5] if len(categories) > 5 else categories
    flags = detect_unusual_spending(transactions, budgets)

    return ExpenseSummaryResult(
        total_income=total_income,
        total_expenses=total_expenses,
        net_savings=net_savings,
        savings_rate=savings_rate,
        essential_spending=essential_spending,
        non_essential_spending=non_essential_spending,
        essential_percentage=essential_pct,
        non_essential_percentage=non_essential_pct,
        transaction_count=len(transactions),
        income_transaction_count=income_count,
        expense_transaction_count=expense_count,
        month_over_month=mom_result,
        category_breakdown=categories,
        largest_categories=largest,
        spending_flags=flags,
    )
