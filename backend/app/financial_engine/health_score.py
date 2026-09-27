from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Optional, Union
from app.financial_engine.constants import (
    DECIMAL_ONE_HUNDRED,
    DECIMAL_ZERO,
    DEFAULT_HEALTH_WEIGHTS,
)
from app.financial_engine.core_metrics import (
    calculate_debt_to_income_ratio,
    calculate_disposable_income,
    calculate_emergency_fund_status,
    calculate_savings_rate,
)
from app.financial_engine.helpers import (
    quantize_percentage,
    to_decimal,
)

@dataclass(frozen=True)
class FinancialHealthScoreResult:
    overall_score: Decimal
    grade: str
    component_scores: Dict[str, Decimal]
    weights_applied: Dict[str, Decimal]
    summary_insights: Dict[str, str]

def calculate_financial_health_score(
    monthly_income: Union[int, float, str, Decimal],
    essential_expenses: Union[int, float, str, Decimal],
    monthly_debt_payments: Union[int, float, str, Decimal],
    current_savings: Union[int, float, str, Decimal],
    custom_weights: Optional[Dict[str, Decimal]] = None,
    budget_discipline_pct: Optional[Union[int, float, str, Decimal]] = None,
    goal_progress_pct: Optional[Union[int, float, str, Decimal]] = None,
) -> FinancialHealthScoreResult:
    inc = to_decimal(monthly_income, allow_negative=False, name="monthly_income")
    ess = to_decimal(essential_expenses, allow_negative=False, name="essential_expenses")
    debt = to_decimal(monthly_debt_payments, allow_negative=False, name="monthly_debt_payments")
    sav = to_decimal(current_savings, allow_negative=False, name="current_savings")

    weights = custom_weights or DEFAULT_HEALTH_WEIGHTS

    disp = calculate_disposable_income(inc, ess, debt)
    sav_rate = calculate_savings_rate(disp, inc)

    if sav_rate <= DECIMAL_ZERO:
        savings_score = DECIMAL_ZERO
    elif sav_rate >= Decimal("20.00"):
        savings_score = DECIMAL_ONE_HUNDRED
    else:
        savings_score = (sav_rate / Decimal("20.00")) * DECIMAL_ONE_HUNDRED

    dti = calculate_debt_to_income_ratio(debt, inc)
    if inc <= DECIMAL_ZERO and debt > DECIMAL_ZERO:
        debt_score = DECIMAL_ZERO
    elif dti <= Decimal("20.00"):
        debt_score = DECIMAL_ONE_HUNDRED
    elif dti >= Decimal("50.00"):
        debt_score = DECIMAL_ZERO
    else:
        debt_score = Decimal("100.00") - ((dti - Decimal("20.00")) / Decimal("30.00")) * Decimal("100.00")

    ef_status = calculate_emergency_fund_status(sav, ess, target_months=Decimal("6.00"))
    months_covered = ef_status.months_covered

    if months_covered >= Decimal("6.00"):
        emergency_score = DECIMAL_ONE_HUNDRED
    elif months_covered <= DECIMAL_ZERO:
        emergency_score = DECIMAL_ZERO
    else:
        emergency_score = (months_covered / Decimal("6.00")) * DECIMAL_ONE_HUNDRED

    if budget_discipline_pct is not None:
        b_val = to_decimal(budget_discipline_pct, allow_negative=False, name="budget_discipline_pct")
        budget_score = min(DECIMAL_ONE_HUNDRED, max(DECIMAL_ZERO, b_val))
    else:
        budget_score = Decimal("85.00")

    if goal_progress_pct is not None:
        g_val = to_decimal(goal_progress_pct, allow_negative=False, name="goal_progress_pct")
        goal_score = min(DECIMAL_ONE_HUNDRED, max(DECIMAL_ZERO, g_val))
    else:
        goal_score = Decimal("80.00")

    comp_scores = {
        "savings_rate": quantize_percentage(savings_score),
        "debt_to_income": quantize_percentage(debt_score),
        "emergency_fund": quantize_percentage(emergency_score),
        "budget_discipline": quantize_percentage(budget_score),
        "goal_progress": quantize_percentage(goal_score),
    }

    weighted_total = sum(comp_scores[k] * weights[k] for k in weights if k in comp_scores)
    overall = quantize_percentage(min(DECIMAL_ONE_HUNDRED, max(DECIMAL_ZERO, weighted_total)))

    if overall >= Decimal("85.00"):
        grade = "Excellent"
    elif overall >= Decimal("70.00"):
        grade = "Good"
    elif overall >= Decimal("55.00"):
        grade = "Fair"
    elif overall >= Decimal("40.00"):
        grade = "Needs Attention"
    else:
        grade = "Critical"

    insights = {
        "savings_rate": f"Savings rate is {sav_rate}% (Score: {comp_scores['savings_rate']}/100)",
        "debt_to_income": f"DTI is {dti}% (Score: {comp_scores['debt_to_income']}/100)",
        "emergency_fund": f"Emergency runway: {months_covered} months (Score: {comp_scores['emergency_fund']}/100)",
        "budget_discipline": f"Budget discipline score: {comp_scores['budget_discipline']}/100",
        "goal_progress": f"Goal progress score: {comp_scores['goal_progress']}/100",
    }

    return FinancialHealthScoreResult(
        overall_score=overall,
        grade=grade,
        component_scores=comp_scores,
        weights_applied=weights,
        summary_insights=insights,
    )
