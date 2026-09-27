from dataclasses import dataclass
from decimal import Decimal
from typing import Union
from app.financial_engine.constants import (
    DECIMAL_ONE_HUNDRED,
    DECIMAL_ZERO,
    DEFAULT_EMERGENCY_MONTHS,
)
from app.financial_engine.helpers import (
    quantize_currency,
    quantize_percentage,
    safe_divide,
    to_decimal,
)

@dataclass(frozen=True)
class BudgetVarianceResult:
    actual: Decimal
    budgeted: Decimal
    variance: Decimal
    variance_percentage: Decimal
    status: str
    is_over_budget: bool

@dataclass(frozen=True)
class EmergencyFundResult:
    current_savings: Decimal
    monthly_essential_expenses: Decimal
    months_covered: Decimal
    target_months: Decimal
    target_amount: Decimal
    shortfall: Decimal
    surplus: Decimal
    is_adequate: bool
    status_label: str

def calculate_disposable_income(
    monthly_income: Union[int, float, str, Decimal],
    essential_expenses: Union[int, float, str, Decimal],
    monthly_debt_payments: Union[int, float, str, Decimal] = DECIMAL_ZERO,
    other_discretionary_expenses: Union[int, float, str, Decimal] = DECIMAL_ZERO,
) -> Decimal:
    inc = to_decimal(monthly_income, allow_negative=False, name="monthly_income")
    ess = to_decimal(essential_expenses, allow_negative=False, name="essential_expenses")
    debt = to_decimal(monthly_debt_payments, allow_negative=False, name="monthly_debt_payments")
    other = to_decimal(other_discretionary_expenses, allow_negative=False, name="other_discretionary_expenses")

    disposable = inc - ess - debt - other
    return quantize_currency(disposable)

def calculate_savings_rate(
    monthly_savings_or_surplus: Union[int, float, str, Decimal],
    monthly_income: Union[int, float, str, Decimal],
) -> Decimal:
    savings = to_decimal(monthly_savings_or_surplus, allow_negative=True, name="monthly_savings")
    income = to_decimal(monthly_income, allow_negative=False, name="monthly_income")

    if income <= DECIMAL_ZERO:
        return DECIMAL_ZERO

    rate = (savings / income) * DECIMAL_ONE_HUNDRED
    return quantize_percentage(rate)

def calculate_expense_ratio(
    expenses: Union[int, float, str, Decimal],
    income: Union[int, float, str, Decimal],
) -> Decimal:
    exp = to_decimal(expenses, allow_negative=False, name="expenses")
    inc = to_decimal(income, allow_negative=False, name="income")

    if inc <= DECIMAL_ZERO:
        return DECIMAL_ONE_HUNDRED if exp > DECIMAL_ZERO else DECIMAL_ZERO

    ratio = (exp / inc) * DECIMAL_ONE_HUNDRED
    return quantize_percentage(ratio)

def calculate_debt_to_income_ratio(
    monthly_debt_payments: Union[int, float, str, Decimal],
    monthly_gross_income: Union[int, float, str, Decimal],
) -> Decimal:
    debt = to_decimal(monthly_debt_payments, allow_negative=False, name="monthly_debt_payments")
    income = to_decimal(monthly_gross_income, allow_negative=False, name="monthly_gross_income")

    if income <= DECIMAL_ZERO:
        return DECIMAL_ONE_HUNDRED if debt > DECIMAL_ZERO else DECIMAL_ZERO

    dti = (debt / income) * DECIMAL_ONE_HUNDRED
    return quantize_percentage(dti)

def calculate_budget_variance(
    actual_amount: Union[int, float, str, Decimal],
    budgeted_amount: Union[int, float, str, Decimal],
    is_income_category: bool = False,
) -> BudgetVarianceResult:
    actual = quantize_currency(to_decimal(actual_amount, allow_negative=False, name="actual_amount"))
    budgeted = quantize_currency(to_decimal(budgeted_amount, allow_negative=False, name="budgeted_amount"))

    variance = quantize_currency(actual - budgeted)

    if budgeted == DECIMAL_ZERO:
        pct_var = DECIMAL_ZERO if actual == DECIMAL_ZERO else DECIMAL_ONE_HUNDRED
    else:
        pct_var = quantize_percentage((variance / budgeted) * DECIMAL_ONE_HUNDRED)

    if is_income_category:
        if variance > DECIMAL_ZERO:
            status = "favorable"
        elif variance < DECIMAL_ZERO:
            status = "unfavorable"
        else:
            status = "on_target"
        is_over = False
    else:
        if variance > DECIMAL_ZERO:
            status = "unfavorable"
            is_over = True
        elif variance < DECIMAL_ZERO:
            status = "favorable"
            is_over = False
        else:
            status = "on_target"
            is_over = False

    return BudgetVarianceResult(
        actual=actual,
        budgeted=budgeted,
        variance=variance,
        variance_percentage=pct_var,
        status=status,
        is_over_budget=is_over,
    )

def calculate_emergency_fund_status(
    emergency_savings: Union[int, float, str, Decimal],
    monthly_essential_expenses: Union[int, float, str, Decimal],
    target_months: Union[int, float, str, Decimal] = DEFAULT_EMERGENCY_MONTHS,
) -> EmergencyFundResult:
    savings = quantize_currency(to_decimal(emergency_savings, allow_negative=False, name="emergency_savings"))
    expenses = quantize_currency(to_decimal(monthly_essential_expenses, allow_negative=False, name="monthly_essential_expenses"))
    target_m = to_decimal(target_months, allow_negative=False, name="target_months")

    target_amt = quantize_currency(expenses * target_m)

    if expenses <= DECIMAL_ZERO:
        months_covered = Decimal("999.00") if savings > DECIMAL_ZERO else DECIMAL_ZERO
        shortfall = DECIMAL_ZERO
        surplus = savings
        is_adequate = True
        status_label = "optimal"
    else:
        months_covered = quantize_percentage(savings / expenses)
        if savings >= target_amt:
            shortfall = DECIMAL_ZERO
            surplus = quantize_currency(savings - target_amt)
            is_adequate = True
            status_label = "optimal" if months_covered >= Decimal("6.00") else "adequate"
        else:
            shortfall = quantize_currency(target_amt - savings)
            surplus = DECIMAL_ZERO
            is_adequate = months_covered >= Decimal("3.00")
            if months_covered < Decimal("1.00"):
                status_label = "critical"
            elif months_covered < Decimal("3.00"):
                status_label = "insufficient"
            else:
                status_label = "adequate"

    return EmergencyFundResult(
        current_savings=savings,
        monthly_essential_expenses=expenses,
        months_covered=months_covered,
        target_months=target_m,
        target_amount=target_amt,
        shortfall=shortfall,
        surplus=surplus,
        is_adequate=is_adequate,
        status_label=status_label,
    )
