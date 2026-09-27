from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from app.financial_engine.constants import (
    DECIMAL_ONE_HUNDRED,
    DECIMAL_ZERO,
    DEFAULT_EMERGENCY_MONTHS,
)
from app.financial_engine.core_metrics import (
    calculate_debt_to_income_ratio,
    calculate_disposable_income,
    calculate_emergency_fund_status,
    calculate_savings_rate,
)
from app.financial_engine.goals import calculate_goal_completion_timeline
from app.financial_engine.health_score import calculate_financial_health_score
from app.financial_engine.helpers import (
    quantize_currency,
    quantize_percentage,
    to_decimal,
)

@dataclass(frozen=True)
class PurchaseAffordabilityResult:
    purchase_price: Decimal
    is_recurring: bool
    is_affordable: bool
    affordability_grade: str
    impact_on_savings: Decimal
    new_savings_balance: Decimal
    new_monthly_disposable_income: Decimal
    impact_on_emergency_fund_months: Decimal
    shortfall: Decimal
    recommended_action: str
    warnings: List[str]

@dataclass(frozen=True)
class ScenarioImpactResult:
    scenario_type: str
    change_amount: Decimal
    previous_savings: Decimal
    new_savings: Decimal
    savings_delta: Decimal
    previous_disposable_income: Decimal
    new_disposable_income: Decimal
    disposable_income_delta: Decimal
    previous_savings_rate: Decimal
    new_savings_rate: Decimal
    is_sustainable: bool
    goal_timeline_impacts: List[Dict[str, Any]]
    summary_message: str

def evaluate_purchase_affordability(
    purchase_amount: Union[int, float, str, Decimal],
    current_savings: Union[int, float, str, Decimal],
    monthly_income: Union[int, float, str, Decimal],
    monthly_essential_expenses: Union[int, float, str, Decimal],
    monthly_debt_payments: Union[int, float, str, Decimal] = DECIMAL_ZERO,
    is_recurring: bool = False,
    emergency_months_threshold: Union[int, float, str, Decimal] = DEFAULT_EMERGENCY_MONTHS,
) -> PurchaseAffordabilityResult:
    price = quantize_currency(to_decimal(purchase_amount, allow_negative=False, name="purchase_amount"))
    savings = quantize_currency(to_decimal(current_savings, allow_negative=False, name="current_savings"))
    income = quantize_currency(to_decimal(monthly_income, allow_negative=False, name="monthly_income"))
    expenses = quantize_currency(to_decimal(monthly_essential_expenses, allow_negative=False, name="monthly_essential_expenses"))
    debt = quantize_currency(to_decimal(monthly_debt_payments, allow_negative=False, name="monthly_debt_payments"))
    target_months = to_decimal(emergency_months_threshold, allow_negative=False, name="emergency_months_threshold")

    current_disposable = calculate_disposable_income(income, expenses, debt)
    emergency_target = quantize_currency(expenses * target_months)
    warnings: List[str] = []

    if is_recurring:
        new_expenses = expenses + price
        new_disposable = calculate_disposable_income(income, new_expenses, debt)
        impact_savings = DECIMAL_ZERO
        new_savings = savings
        new_ef_status = calculate_emergency_fund_status(savings, new_expenses, target_months)

        if new_disposable < DECIMAL_ZERO:
            is_affordable = False
            grade = "unaffordable"
            shortfall = quantize_currency(abs(new_disposable))
            action = "Do not proceed. This recurring expense results in a negative monthly cash flow."
            warnings.append(f"Monthly cash flow deficit of ${shortfall}.")
        elif current_disposable > DECIMAL_ZERO and new_disposable < (current_disposable * Decimal("0.20")):
            is_affordable = True
            grade = "stretched"
            shortfall = DECIMAL_ZERO
            action = "Caution. This recurring commitment consumes more than 80% of your current disposable income."
            warnings.append("Severely reduces monthly discretionary buffer.")
        else:
            is_affordable = True
            grade = "safe"
            shortfall = DECIMAL_ZERO
            action = "Affordable. Monthly cash flow comfortably accommodates this recurring expense."

        return PurchaseAffordabilityResult(
            purchase_price=price,
            is_recurring=True,
            is_affordable=is_affordable,
            affordability_grade=grade,
            impact_on_savings=impact_savings,
            new_savings_balance=new_savings,
            new_monthly_disposable_income=new_disposable,
            impact_on_emergency_fund_months=new_ef_status.months_covered,
            shortfall=shortfall,
            recommended_action=action,
            warnings=warnings,
        )

    # One-time purchase
    impact_savings = price
    new_savings = savings - price
    new_disposable = current_disposable

    if price > savings:
        is_affordable = False
        grade = "unaffordable"
        shortfall = quantize_currency(price - savings)
        action = "Unaffordable. Purchase amount exceeds total current liquid savings."
        warnings.append(f"Shortfall of ${shortfall} from current savings.")
        ef_months = DECIMAL_ZERO
    elif new_savings < emergency_target:
        ef_status = calculate_emergency_fund_status(new_savings, expenses, target_months)
        ef_months = ef_status.months_covered
        shortfall = ef_status.shortfall

        if ef_months < Decimal("3.00"):
            is_affordable = False
            grade = "unaffordable"
            action = "Not recommended. This purchase would deplete your emergency fund below the critical 3-month threshold."
            warnings.append(f"Leaves only {ef_months} months of emergency runway (minimum recommended: 3 months).")
        else:
            is_affordable = True
            grade = "stretched"
            action = "Proceed with caution. Purchase depletes emergency savings below the optimal target."
            warnings.append(f"Emergency savings reduced to {ef_months} months.")
    else:
        ef_status = calculate_emergency_fund_status(new_savings, expenses, target_months)
        ef_months = ef_status.months_covered
        is_affordable = True
        grade = "safe"
        shortfall = DECIMAL_ZERO
        action = "Affordable. Purchase can be made while fully preserving emergency buffer."

    return PurchaseAffordabilityResult(
        purchase_price=price,
        is_recurring=False,
        is_affordable=is_affordable,
        affordability_grade=grade,
        impact_on_savings=impact_savings,
        new_savings_balance=quantize_currency(new_savings),
        new_monthly_disposable_income=new_disposable,
        impact_on_emergency_fund_months=ef_months,
        shortfall=shortfall,
        recommended_action=action,
        warnings=warnings,
    )

def simulate_scenario_impact(
    monthly_income: Union[int, float, str, Decimal],
    monthly_essential_expenses: Union[int, float, str, Decimal],
    monthly_debt_payments: Union[int, float, str, Decimal],
    current_savings: Union[int, float, str, Decimal],
    scenario_type: str,
    change_amount: Union[int, float, str, Decimal],
    is_recurring: bool = False,
    active_goals: Optional[List[Dict[str, Any]]] = None,
) -> ScenarioImpactResult:
    inc = quantize_currency(to_decimal(monthly_income, allow_negative=False, name="monthly_income"))
    ess = quantize_currency(to_decimal(monthly_essential_expenses, allow_negative=False, name="monthly_essential_expenses"))
    debt = quantize_currency(to_decimal(monthly_debt_payments, allow_negative=False, name="monthly_debt_payments"))
    sav = quantize_currency(to_decimal(current_savings, allow_negative=False, name="current_savings"))
    amt = to_decimal(change_amount, allow_negative=True, name="change_amount")

    prev_disp = calculate_disposable_income(inc, ess, debt)
    prev_sav_rate = calculate_savings_rate(prev_disp, inc)

    new_inc = inc
    new_ess = ess
    new_sav = sav

    if scenario_type in ("one_time_purchase", "unexpected_expense"):
        cost = abs(amt)
        new_sav = sav - cost
        sav_delta = -cost
        disp_delta = DECIMAL_ZERO
        new_disp = prev_disp
        new_sav_rate = prev_sav_rate
    elif scenario_type == "income_change":
        new_inc = max(DECIMAL_ZERO, inc + amt)
        sav_delta = DECIMAL_ZERO
        new_disp = calculate_disposable_income(new_inc, ess, debt)
        disp_delta = new_disp - prev_disp
        new_sav_rate = calculate_savings_rate(new_disp, new_inc)
    elif scenario_type == "expense_change":
        new_ess = max(DECIMAL_ZERO, ess + amt)
        sav_delta = DECIMAL_ZERO
        new_disp = calculate_disposable_income(inc, new_ess, debt)
        disp_delta = new_disp - prev_disp
        new_sav_rate = calculate_savings_rate(new_disp, inc)
    else:
        raise ValueError(f"Unknown scenario_type: {scenario_type}")

    is_sustainable = (new_disp >= DECIMAL_ZERO) and (new_sav >= DECIMAL_ZERO)

    goal_impacts: List[Dict[str, Any]] = []
    if active_goals:
        for g in active_goals:
            target = to_decimal(g.get("target_amount", DECIMAL_ZERO))
            curr = to_decimal(g.get("current_amount", DECIMAL_ZERO))
            prev_contrib = to_decimal(g.get("monthly_contribution", DECIMAL_ZERO))

            prev_timeline = calculate_goal_completion_timeline(target, curr, prev_contrib)

            if disp_delta < DECIMAL_ZERO and prev_disp > DECIMAL_ZERO:
                ratio = max(DECIMAL_ZERO, new_disp / prev_disp)
                new_contrib = quantize_currency(prev_contrib * ratio)
            elif disp_delta > DECIMAL_ZERO and prev_disp > DECIMAL_ZERO:
                ratio = new_disp / prev_disp
                new_contrib = quantize_currency(prev_contrib * ratio)
            else:
                new_contrib = prev_contrib

            new_timeline = calculate_goal_completion_timeline(target, curr, new_contrib)

            timeline_diff = (
                new_timeline.months_to_complete - prev_timeline.months_to_complete
                if (new_timeline.is_achievable and prev_timeline.is_achievable)
                else None
            )

            goal_impacts.append({
                "goal_id": g.get("id"),
                "goal_name": g.get("name"),
                "previous_months_to_complete": prev_timeline.months_to_complete,
                "new_months_to_complete": new_timeline.months_to_complete,
                "timeline_delay_months": timeline_diff,
                "previous_monthly_contribution": prev_contrib,
                "new_monthly_contribution": new_contrib,
            })

    summary = (
        f"Scenario [{scenario_type}]: Savings change: ${quantize_currency(sav_delta)}, "
        f"Disposable Income change: ${quantize_currency(disp_delta)}/mo. "
        f"Status: {'Sustainable' if is_sustainable else 'Deficit/Unsustainable'}."
    )

    return ScenarioImpactResult(
        scenario_type=scenario_type,
        change_amount=quantize_currency(amt),
        previous_savings=sav,
        new_savings=quantize_currency(new_sav),
        savings_delta=quantize_currency(sav_delta),
        previous_disposable_income=prev_disp,
        new_disposable_income=quantize_currency(new_disp),
        disposable_income_delta=quantize_currency(disp_delta),
        previous_savings_rate=prev_sav_rate,
        new_savings_rate=new_sav_rate,
        is_sustainable=is_sustainable,
        goal_timeline_impacts=goal_impacts,
        summary_message=summary,
    )


@dataclass(frozen=True)
class FinancialSnapshot:
    monthly_income: Decimal
    monthly_essential_expenses: Decimal
    monthly_debt_payments: Decimal
    monthly_disposable_income: Decimal
    current_savings: Decimal
    savings_rate: Decimal
    debt_to_income_ratio: Decimal
    emergency_fund_months: Decimal
    emergency_fund_status: str
    daily_safe_to_spend: Decimal
    financial_health_score: Decimal
    financial_health_grade: str


@dataclass(frozen=True)
class FinancialSnapshotDelta:
    monthly_income_delta: Decimal
    monthly_essential_expenses_delta: Decimal
    monthly_disposable_income_delta: Decimal
    savings_delta: Decimal
    savings_rate_delta: Decimal
    debt_to_income_delta: Decimal
    emergency_fund_months_delta: Decimal
    daily_safe_to_spend_delta: Decimal
    financial_health_score_delta: Decimal


@dataclass(frozen=True)
class GoalScenarioImpact:
    goal_id: str
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    previous_monthly_contribution: Decimal
    new_monthly_contribution: Decimal
    previous_months_to_complete: int
    new_months_to_complete: int
    timeline_delay_months: Optional[int]
    is_still_feasible: bool
    explanation: str


@dataclass(frozen=True)
class DetailedScenarioResult:
    scenario_id: str
    scenario_name: str
    scenario_type: str
    amount: Decimal
    timing_months: int
    description: Optional[str]
    is_sustainable: bool
    affordability_verdict: str
    before_state: FinancialSnapshot
    after_state: FinancialSnapshot
    delta: FinancialSnapshotDelta
    goal_impacts: List[GoalScenarioImpact]
    warnings: List[str]
    tradeoffs: List[str]
    recommendation: str


@dataclass(frozen=True)
class ScenarioComparisonResult:
    baseline: FinancialSnapshot
    scenarios: List[DetailedScenarioResult]
    tradeoff_summary: List[Dict[str, Any]]


def build_financial_snapshot(
    monthly_income: Union[int, float, str, Decimal],
    monthly_essential_expenses: Union[int, float, str, Decimal],
    monthly_debt_payments: Union[int, float, str, Decimal],
    current_savings: Union[int, float, str, Decimal],
    daily_safe_to_spend: Optional[Union[int, float, str, Decimal]] = None,
    emergency_months_threshold: Union[int, float, str, Decimal] = DEFAULT_EMERGENCY_MONTHS,
) -> FinancialSnapshot:
    inc = quantize_currency(to_decimal(monthly_income, allow_negative=False, name="monthly_income"))
    ess = quantize_currency(to_decimal(monthly_essential_expenses, allow_negative=False, name="monthly_essential_expenses"))
    debt = quantize_currency(to_decimal(monthly_debt_payments, allow_negative=False, name="monthly_debt_payments"))
    sav = quantize_currency(to_decimal(current_savings, allow_negative=False, name="current_savings"))
    target_ef_months = to_decimal(emergency_months_threshold, allow_negative=False, name="emergency_months_threshold")

    disp = calculate_disposable_income(inc, ess, debt)
    sav_rate = calculate_savings_rate(disp, inc)
    dti = calculate_debt_to_income_ratio(debt, inc)
    ef_status = calculate_emergency_fund_status(sav, ess, target_ef_months)

    if daily_safe_to_spend is not None:
        safe_daily = quantize_currency(to_decimal(daily_safe_to_spend, allow_negative=True))
    else:
        # 30-day standard cycle estimate: (disp * 0.5) / 30
        safe_daily = quantize_currency(max(DECIMAL_ZERO, disp * Decimal("0.50")) / Decimal("30"))

    health_res = calculate_financial_health_score(
        monthly_income=inc,
        essential_expenses=ess,
        monthly_debt_payments=debt,
        current_savings=sav,
    )

    return FinancialSnapshot(
        monthly_income=inc,
        monthly_essential_expenses=ess,
        monthly_debt_payments=debt,
        monthly_disposable_income=disp,
        current_savings=sav,
        savings_rate=sav_rate,
        debt_to_income_ratio=dti,
        emergency_fund_months=ef_status.months_covered,
        emergency_fund_status=ef_status.status_label,
        daily_safe_to_spend=safe_daily,
        financial_health_score=health_res.overall_score,
        financial_health_grade=health_res.grade,
    )


def simulate_detailed_decision_scenario(
    monthly_income: Union[int, float, str, Decimal],
    monthly_essential_expenses: Union[int, float, str, Decimal],
    monthly_debt_payments: Union[int, float, str, Decimal],
    current_savings: Union[int, float, str, Decimal],
    scenario_type: str,
    amount: Union[int, float, str, Decimal],
    scenario_id: str = "scenario_1",
    scenario_name: str = "Proposed Decision",
    timing_months: int = 0,
    description: Optional[str] = None,
    daily_safe_to_spend: Optional[Union[int, float, str, Decimal]] = None,
    emergency_months_threshold: Union[int, float, str, Decimal] = DEFAULT_EMERGENCY_MONTHS,
    active_goals: Optional[List[Dict[str, Any]]] = None,
) -> DetailedScenarioResult:
    normalized_type = scenario_type.lower().strip()
    amt = to_decimal(amount, allow_negative=True, name="amount")
    abs_amt = abs(amt)

    # 1. Base snapshot
    before = build_financial_snapshot(
        monthly_income=monthly_income,
        monthly_essential_expenses=monthly_essential_expenses,
        monthly_debt_payments=monthly_debt_payments,
        current_savings=current_savings,
        daily_safe_to_spend=daily_safe_to_spend,
        emergency_months_threshold=emergency_months_threshold,
    )

    # 2. Compute after metrics
    new_inc = before.monthly_income
    new_ess = before.monthly_essential_expenses
    new_debt = before.monthly_debt_payments
    new_sav = before.current_savings

    warnings: List[str] = []
    tradeoffs: List[str] = []

    # Handle timing delay: if timing_months > 0, project savings growth before purchase
    projected_sav_at_timing = before.current_savings
    if timing_months > 0 and before.monthly_disposable_income > DECIMAL_ZERO:
        monthly_savings_addition = max(DECIMAL_ZERO, before.monthly_disposable_income * Decimal("0.50"))
        projected_sav_at_timing += monthly_savings_addition * Decimal(str(timing_months))

    if normalized_type in ("one_time_purchase", "purchase", "unexpected_expense"):
        # Depletes savings
        savings_baseline = projected_sav_at_timing if timing_months > 0 else before.current_savings
        new_sav = max(DECIMAL_ZERO, savings_baseline - abs_amt)

        if abs_amt > savings_baseline:
            warnings.append(f"Expense of ${abs_amt} exceeds available liquid savings (${savings_baseline}).")
        if new_sav < (before.monthly_essential_expenses * Decimal("3.00")):
            warnings.append(f"Reduces emergency reserve to {quantize_currency(new_sav / before.monthly_essential_expenses if before.monthly_essential_expenses > 0 else 0)} months.")

        tradeoffs.append(f"Reduces liquid cash reserves by ${abs_amt}.")
        if timing_months > 0:
            tradeoffs.append(f"Delayed by {timing_months} months: Allowed accumulating savings before purchase.")

    elif normalized_type in ("new_recurring_expense", "recurring_expense", "expense_increase"):
        new_ess = before.monthly_essential_expenses + abs_amt
        tradeoffs.append(f"Increases monthly fixed outflow by ${abs_amt}/month.")

    elif normalized_type in ("income_change", "income_increase", "income_decrease"):
        new_inc = max(DECIMAL_ZERO, before.monthly_income + amt)
        if amt >= DECIMAL_ZERO:
            tradeoffs.append(f"Increases monthly income by ${abs_amt}/month (+{quantize_percentage((abs_amt / before.monthly_income * DECIMAL_ONE_HUNDRED) if before.monthly_income > 0 else 0)}%).")
        else:
            tradeoffs.append(f"Reduces monthly income by ${abs_amt}/month.")

    else:
        raise ValueError(f"Unsupported scenario_type: '{scenario_type}'. Supported: 'one_time_purchase', 'new_recurring_expense', 'income_change', 'unexpected_expense'.")

    # Recompute daily safe-to-spend for after state
    new_disp = calculate_disposable_income(new_inc, new_ess, new_debt)
    new_safe_daily = quantize_currency(max(DECIMAL_ZERO, new_disp * Decimal("0.50")) / Decimal("30"))

    after = build_financial_snapshot(
        monthly_income=new_inc,
        monthly_essential_expenses=new_ess,
        monthly_debt_payments=new_debt,
        current_savings=new_sav,
        daily_safe_to_spend=new_safe_daily,
        emergency_months_threshold=emergency_months_threshold,
    )

    # 3. Calculate deltas
    delta = FinancialSnapshotDelta(
        monthly_income_delta=quantize_currency(after.monthly_income - before.monthly_income),
        monthly_essential_expenses_delta=quantize_currency(after.monthly_essential_expenses - before.monthly_essential_expenses),
        monthly_disposable_income_delta=quantize_currency(after.monthly_disposable_income - before.monthly_disposable_income),
        savings_delta=quantize_currency(after.current_savings - before.current_savings),
        savings_rate_delta=quantize_percentage(after.savings_rate - before.savings_rate),
        debt_to_income_delta=quantize_percentage(after.debt_to_income_ratio - before.debt_to_income_ratio),
        emergency_fund_months_delta=quantize_currency(after.emergency_fund_months - before.emergency_fund_months),
        daily_safe_to_spend_delta=quantize_currency(after.daily_safe_to_spend - before.daily_safe_to_spend),
        financial_health_score_delta=quantize_currency(after.financial_health_score - before.financial_health_score),
    )

    # 4. Evaluate Goal impacts
    goal_impacts: List[GoalScenarioImpact] = []
    if active_goals:
        for g in active_goals:
            target = quantize_currency(to_decimal(g.get("target_amount", DECIMAL_ZERO), allow_negative=False))
            curr = quantize_currency(to_decimal(g.get("current_amount", DECIMAL_ZERO), allow_negative=False))
            prev_contrib = quantize_currency(to_decimal(g.get("monthly_contribution", DECIMAL_ZERO), allow_negative=False))

            prev_timeline = calculate_goal_completion_timeline(target, curr, prev_contrib)

            # Adjust contribution according to disposable income change
            if delta.monthly_disposable_income_delta < DECIMAL_ZERO and before.monthly_disposable_income > DECIMAL_ZERO:
                ratio = max(DECIMAL_ZERO, after.monthly_disposable_income / before.monthly_disposable_income)
                new_contrib = quantize_currency(prev_contrib * ratio)
            elif delta.monthly_disposable_income_delta > DECIMAL_ZERO and before.monthly_disposable_income > DECIMAL_ZERO:
                ratio = after.monthly_disposable_income / before.monthly_disposable_income
                new_contrib = quantize_currency(prev_contrib * ratio)
            else:
                new_contrib = prev_contrib

            new_timeline = calculate_goal_completion_timeline(target, curr, new_contrib)

            delay_months = (
                new_timeline.months_to_complete - prev_timeline.months_to_complete
                if (new_timeline.is_achievable and prev_timeline.is_achievable)
                else None
            )

            is_feasible = new_timeline.is_achievable and (new_contrib <= after.monthly_disposable_income or after.monthly_disposable_income >= DECIMAL_ZERO)
            explanation = (
                f"Projected completion delayed by {delay_months} months."
                if (delay_months and delay_months > 0)
                else "No completion delay projected."
            )

            goal_impacts.append(
                GoalScenarioImpact(
                    goal_id=str(g.get("id", "goal")),
                    goal_name=str(g.get("name", "Goal")),
                    target_amount=target,
                    current_amount=curr,
                    previous_monthly_contribution=prev_contrib,
                    new_monthly_contribution=new_contrib,
                    previous_months_to_complete=prev_timeline.months_to_complete,
                    new_months_to_complete=new_timeline.months_to_complete,
                    timeline_delay_months=delay_months,
                    is_still_feasible=is_feasible,
                    explanation=explanation,
                )
            )

    # 5. Sustainability & Verdict
    is_sustainable = (after.monthly_disposable_income >= DECIMAL_ZERO) and (after.current_savings >= DECIMAL_ZERO)

    if not is_sustainable or after.emergency_fund_months < Decimal("1.00"):
        verdict = "unaffordable"
        recommendation = "Not recommended under current financial conditions. Leads to severe cash flow deficit or emergency depletion."
    elif after.emergency_fund_months < Decimal("3.00") or after.monthly_disposable_income < (before.monthly_disposable_income * Decimal("0.30")):
        verdict = "stretched"
        recommendation = "Feasible with caution. Consider building a larger liquidity buffer or delaying the decision."
    else:
        verdict = "safe"
        recommendation = "Comfortably affordable. Financial health, emergency runway, and goals remain intact."

    return DetailedScenarioResult(
        scenario_id=scenario_id,
        scenario_name=scenario_name,
        scenario_type=normalized_type,
        amount=quantize_currency(amt),
        timing_months=timing_months,
        description=description,
        is_sustainable=is_sustainable,
        affordability_verdict=verdict,
        before_state=before,
        after_state=after,
        delta=delta,
        goal_impacts=goal_impacts,
        warnings=warnings,
        tradeoffs=tradeoffs,
        recommendation=recommendation,
    )


def compare_decision_scenarios(
    monthly_income: Union[int, float, str, Decimal],
    monthly_essential_expenses: Union[int, float, str, Decimal],
    monthly_debt_payments: Union[int, float, str, Decimal],
    current_savings: Union[int, float, str, Decimal],
    scenarios_list: List[Dict[str, Any]],
    active_goals: Optional[List[Dict[str, Any]]] = None,
) -> ScenarioComparisonResult:
    baseline = build_financial_snapshot(
        monthly_income=monthly_income,
        monthly_essential_expenses=monthly_essential_expenses,
        monthly_debt_payments=monthly_debt_payments,
        current_savings=current_savings,
    )

    results: List[DetailedScenarioResult] = []
    tradeoffs: List[Dict[str, Any]] = []

    # Limit to 3 scenarios
    for idx, sc in enumerate(scenarios_list[:3]):
        sc_id = str(sc.get("id", f"scenario_{idx + 1}"))
        sc_name = str(sc.get("name", f"Scenario {chr(65 + idx)}"))
        sc_type = str(sc.get("type", "one_time_purchase"))
        sc_amount = to_decimal(sc.get("amount", DECIMAL_ZERO))
        sc_timing = int(sc.get("timing_months", 0))
        sc_desc = sc.get("description")

        sim_res = simulate_detailed_decision_scenario(
            monthly_income=monthly_income,
            monthly_essential_expenses=monthly_essential_expenses,
            monthly_debt_payments=monthly_debt_payments,
            current_savings=current_savings,
            scenario_id=sc_id,
            scenario_name=sc_name,
            scenario_type=sc_type,
            amount=sc_amount,
            timing_months=sc_timing,
            description=sc_desc,
            active_goals=active_goals,
        )
        results.append(sim_res)

        tradeoffs.append({
            "scenario_id": sc_id,
            "scenario_name": sc_name,
            "verdict": sim_res.affordability_verdict,
            "ending_savings": str(sim_res.after_state.current_savings),
            "monthly_cash_flow": str(sim_res.after_state.monthly_disposable_income),
            "emergency_runway_months": str(sim_res.after_state.emergency_fund_months),
            "health_score": str(sim_res.after_state.financial_health_score),
            "health_score_change": str(sim_res.delta.financial_health_score_delta),
            "key_tradeoffs": sim_res.tradeoffs,
            "recommendation": sim_res.recommendation,
        })

    return ScenarioComparisonResult(
        baseline=baseline,
        scenarios=results,
        tradeoff_summary=tradeoffs,
    )

