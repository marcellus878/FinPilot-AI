from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple, Union

from app.financial_engine.helpers import (
    quantize_currency,
    quantize_percentage,
    safe_divide,
    to_decimal,
)
from app.financial_engine.salary_planner import (
    SalaryAllocationResult,
    calculate_salary_allocation,
)


@dataclass
class MonitoringSnapshot:
    monthly_income: Decimal
    monthly_essential_expenses: Decimal
    monthly_discretionary_expenses: Decimal
    monthly_total_expenses: Decimal
    current_savings: Decimal
    monthly_debt_payment: Decimal
    savings_rate: Decimal
    safe_to_spend_daily: Decimal
    emergency_runway_months: Decimal
    emergency_runway_status: str
    financial_health_score: Decimal
    financial_health_grade: str
    budget_variance: Decimal
    recurring_commitments_monthly: Decimal
    active_goals_count: int
    goals_monthly_required: Decimal
    goals_monthly_capacity: Decimal
    goals_feasible: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FinancialChangeItem:
    metric: str
    baseline: Decimal
    current: Decimal
    absolute_change: Decimal
    percentage_change: Decimal
    severity: str  # "low", "medium", "high", "critical"
    source: str = "financial_engine"
    description: str = ""


@dataclass
class ReplanningAssessment:
    replanning_required: bool
    trigger: str  # "nominal", "income_change", "spending_surge", "safe_to_spend_depleted", "emergency_runway_depleted", "goal_infeasible", "recurring_outflow_surge", "budget_overrun"
    severity: str  # "low", "medium", "high", "critical"
    affected_areas: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class PlanComparisonItem:
    area: str
    metric: str
    baseline_value: str
    proposed_value: str
    delta: str
    explanation: str


@dataclass
class PlanComparisonTable:
    items: List[PlanComparisonItem]
    summary: str
    affected_goals: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ReplanningStrategyOption:
    strategy_id: str
    title: str
    description: str
    adjusted_essential: Decimal
    adjusted_savings: Decimal
    adjusted_discretionary: Decimal
    resulting_buffer: Decimal
    impact_on_goals: str
    tradeoffs: List[str] = field(default_factory=list)


def build_monitoring_snapshot(
    monthly_income: Union[int, float, str, Decimal],
    essential_expenses: Union[int, float, str, Decimal],
    discretionary_expenses: Union[int, float, str, Decimal],
    current_savings: Union[int, float, str, Decimal],
    monthly_debt: Union[int, float, str, Decimal] = Decimal("0.00"),
    safe_to_spend_daily: Union[int, float, str, Decimal] = Decimal("0.00"),
    emergency_runway_months: Union[int, float, str, Decimal] = Decimal("0.00"),
    emergency_runway_status: str = "adequate",
    financial_health_score: Union[int, float, str, Decimal] = Decimal("75.00"),
    financial_health_grade: str = "B",
    budget_variance: Union[int, float, str, Decimal] = Decimal("0.00"),
    recurring_commitments_monthly: Union[int, float, str, Decimal] = Decimal("0.00"),
    active_goals_count: int = 0,
    goals_monthly_required: Union[int, float, str, Decimal] = Decimal("0.00"),
    goals_monthly_capacity: Union[int, float, str, Decimal] = Decimal("0.00"),
    goals_feasible: bool = True,
    timestamp: Optional[datetime] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> MonitoringSnapshot:
    """Constructs a validated, quantized MonitoringSnapshot."""
    inc = quantize_currency(to_decimal(monthly_income, allow_negative=False))
    ess = quantize_currency(to_decimal(essential_expenses, allow_negative=False))
    disc = quantize_currency(to_decimal(discretionary_expenses, allow_negative=False))
    tot_exp = quantize_currency(ess + disc)
    sav = quantize_currency(to_decimal(current_savings, allow_negative=False))
    debt = quantize_currency(to_decimal(monthly_debt, allow_negative=False))

    disposable = max(Decimal("0.00"), inc - ess - debt)
    sav_rate = quantize_percentage(safe_divide(disposable, inc) * Decimal("100.00"))

    safe_daily = quantize_currency(to_decimal(safe_to_spend_daily, allow_negative=True))
    runway_months = quantize_currency(to_decimal(emergency_runway_months, allow_negative=False))
    health_pts = quantize_currency(to_decimal(financial_health_score, allow_negative=False))
    variance = quantize_currency(to_decimal(budget_variance, allow_negative=True))
    recurring = quantize_currency(to_decimal(recurring_commitments_monthly, allow_negative=False))

    req_goals = quantize_currency(to_decimal(goals_monthly_required, allow_negative=False))
    cap_goals = quantize_currency(to_decimal(goals_monthly_capacity, allow_negative=False))

    return MonitoringSnapshot(
        monthly_income=inc,
        monthly_essential_expenses=ess,
        monthly_discretionary_expenses=disc,
        monthly_total_expenses=tot_exp,
        current_savings=sav,
        monthly_debt_payment=debt,
        savings_rate=sav_rate,
        safe_to_spend_daily=safe_daily,
        emergency_runway_months=runway_months,
        emergency_runway_status=emergency_runway_status,
        financial_health_score=health_pts,
        financial_health_grade=financial_health_grade,
        budget_variance=variance,
        recurring_commitments_monthly=recurring,
        active_goals_count=active_goals_count,
        goals_monthly_required=req_goals,
        goals_monthly_capacity=cap_goals,
        goals_feasible=goals_feasible,
        timestamp=timestamp or datetime.utcnow(),
        metadata=metadata or {},
    )


def detect_financial_changes(
    baseline: MonitoringSnapshot,
    current: MonitoringSnapshot,
) -> List[FinancialChangeItem]:
    """
    Deterministic comparison engine:
    Evaluates deltas between baseline state and current observed state.
    Calculates percentage change and classifies severity mathematically.
    """
    changes: List[FinancialChangeItem] = []

    # 1. Income Change
    income_delta = current.monthly_income - baseline.monthly_income
    if abs(income_delta) >= Decimal("10.00"):
        pct = quantize_percentage(safe_divide(income_delta, baseline.monthly_income) * Decimal("100.00"))
        if income_delta <= Decimal("-500.00") or pct <= Decimal("-15.00"):
            sev = "critical"
        elif income_delta < Decimal("0.00"):
            sev = "high"
        elif pct >= Decimal("15.00"):
            sev = "medium"
        else:
            sev = "low"

        desc = (
            f"Monthly income decreased by ${abs(income_delta):,.2f} ({abs(pct)}%) from ${baseline.monthly_income:,.2f} to ${current.monthly_income:,.2f}."
            if income_delta < 0
            else f"Monthly income increased by ${income_delta:,.2f} (+{pct}%) from ${baseline.monthly_income:,.2f} to ${current.monthly_income:,.2f}."
        )
        changes.append(
            FinancialChangeItem(
                metric="income",
                baseline=baseline.monthly_income,
                current=current.monthly_income,
                absolute_change=quantize_currency(income_delta),
                percentage_change=pct,
                severity=sev,
                source="financial_engine",
                description=desc,
            )
        )

    # 2. Essential Expenses Change
    ess_delta = current.monthly_essential_expenses - baseline.monthly_essential_expenses
    if abs(ess_delta) >= Decimal("15.00"):
        pct = quantize_percentage(safe_divide(ess_delta, baseline.monthly_essential_expenses) * Decimal("100.00"))
        if ess_delta >= Decimal("500.00") or pct >= Decimal("20.00"):
            sev = "high"
        elif ess_delta > Decimal("0.00"):
            sev = "medium"
        else:
            sev = "low"

        desc = (
            f"Essential living expenses increased by ${ess_delta:,.2f} (+{pct}%) from ${baseline.monthly_essential_expenses:,.2f} to ${current.monthly_essential_expenses:,.2f}."
            if ess_delta > 0
            else f"Essential living expenses decreased by ${abs(ess_delta):,.2f} ({abs(pct)}%) to ${current.monthly_essential_expenses:,.2f}."
        )
        changes.append(
            FinancialChangeItem(
                metric="essential_expenses",
                baseline=baseline.monthly_essential_expenses,
                current=current.monthly_essential_expenses,
                absolute_change=quantize_currency(ess_delta),
                percentage_change=pct,
                severity=sev,
                source="financial_engine",
                description=desc,
            )
        )

    # 3. Discretionary Spending Surge
    disc_delta = current.monthly_discretionary_expenses - baseline.monthly_discretionary_expenses
    if abs(disc_delta) >= Decimal("20.00"):
        pct = quantize_percentage(safe_divide(disc_delta, baseline.monthly_discretionary_expenses) * Decimal("100.00"))
        if disc_delta >= Decimal("400.00") or pct >= Decimal("25.00"):
            sev = "high"
        elif disc_delta > Decimal("0.00"):
            sev = "medium"
        else:
            sev = "low"

        desc = (
            f"Discretionary spending increased by ${disc_delta:,.2f} (+{pct}%) from ${baseline.monthly_discretionary_expenses:,.2f} to ${current.monthly_discretionary_expenses:,.2f}."
            if disc_delta > 0
            else f"Discretionary spending reduced by ${abs(disc_delta):,.2f} ({abs(pct)}%) to ${current.monthly_discretionary_expenses:,.2f}."
        )
        changes.append(
            FinancialChangeItem(
                metric="discretionary_expenses",
                baseline=baseline.monthly_discretionary_expenses,
                current=current.monthly_discretionary_expenses,
                absolute_change=quantize_currency(disc_delta),
                percentage_change=pct,
                severity=sev,
                source="financial_engine",
                description=desc,
            )
        )

    # 4. Recurring Commitments
    rec_delta = current.recurring_commitments_monthly - baseline.recurring_commitments_monthly
    if abs(rec_delta) >= Decimal("10.00"):
        pct = quantize_percentage(safe_divide(rec_delta, baseline.recurring_commitments_monthly) * Decimal("100.00"))
        if rec_delta >= Decimal("300.00") or pct >= Decimal("20.00"):
            sev = "high"
        elif rec_delta > Decimal("0.00"):
            sev = "medium"
        else:
            sev = "low"

        desc = (
            f"Fixed monthly recurring commitments increased by ${rec_delta:,.2f} (+{pct}%) to ${current.recurring_commitments_monthly:,.2f}/month."
            if rec_delta > 0
            else f"Recurring commitments reduced by ${abs(rec_delta):,.2f} to ${current.recurring_commitments_monthly:,.2f}/month."
        )
        changes.append(
            FinancialChangeItem(
                metric="recurring_commitments",
                baseline=baseline.recurring_commitments_monthly,
                current=current.recurring_commitments_monthly,
                absolute_change=quantize_currency(rec_delta),
                percentage_change=pct,
                severity=sev,
                source="financial_engine",
                description=desc,
            )
        )

    # 5. Safe-to-Spend Allowance
    safe_delta = current.safe_to_spend_daily - baseline.safe_to_spend_daily
    if abs(safe_delta) >= Decimal("2.00"):
        pct = quantize_percentage(safe_divide(safe_delta, baseline.safe_to_spend_daily) * Decimal("100.00"))
        if current.safe_to_spend_daily <= Decimal("0.00") or safe_delta <= Decimal("-15.00"):
            sev = "critical"
        elif safe_delta < Decimal("0.00"):
            sev = "high"
        else:
            sev = "low"

        desc = (
            f"Daily safe-to-spend allowance reduced by ${abs(safe_delta):,.2f}/day to ${current.safe_to_spend_daily:,.2f}/day."
            if safe_delta < 0
            else f"Daily safe-to-spend allowance improved by ${safe_delta:,.2f}/day to ${current.safe_to_spend_daily:,.2f}/day."
        )
        changes.append(
            FinancialChangeItem(
                metric="safe_to_spend",
                baseline=baseline.safe_to_spend_daily,
                current=current.safe_to_spend_daily,
                absolute_change=quantize_currency(safe_delta),
                percentage_change=pct,
                severity=sev,
                source="financial_engine",
                description=desc,
            )
        )

    # 6. Emergency Runway Months
    runway_delta = current.emergency_runway_months - baseline.emergency_runway_months
    if abs(runway_delta) >= Decimal("0.20"):
        pct = quantize_percentage(safe_divide(runway_delta, baseline.emergency_runway_months) * Decimal("100.00"))
        if current.emergency_runway_months < Decimal("3.00") or runway_delta <= Decimal("-1.00"):
            sev = "critical"
        elif runway_delta < Decimal("0.00"):
            sev = "high"
        else:
            sev = "low"

        desc = (
            f"Emergency fund runway depleted by {abs(runway_delta)} months from {baseline.emergency_runway_months} mos to {current.emergency_runway_months} mos ({current.emergency_runway_status})."
            if runway_delta < 0
            else f"Emergency fund runway extended by {runway_delta} months to {current.emergency_runway_months} mos."
        )
        changes.append(
            FinancialChangeItem(
                metric="emergency_runway",
                baseline=baseline.emergency_runway_months,
                current=current.emergency_runway_months,
                absolute_change=quantize_currency(runway_delta),
                percentage_change=pct,
                severity=sev,
                source="financial_engine",
                description=desc,
            )
        )

    # 7. Savings Rate
    sav_rate_delta = current.savings_rate - baseline.savings_rate
    if abs(sav_rate_delta) >= Decimal("2.00"):
        if sav_rate_delta <= Decimal("-10.00"):
            sev = "high"
        elif sav_rate_delta < Decimal("0.00"):
            sev = "medium"
        else:
            sev = "low"

        desc = (
            f"Savings rate dropped by {abs(sav_rate_delta)}% from {baseline.savings_rate}% to {current.savings_rate}%."
            if sav_rate_delta < 0
            else f"Savings rate improved by {sav_rate_delta}% to {current.savings_rate}%."
        )
        changes.append(
            FinancialChangeItem(
                metric="savings_rate",
                baseline=baseline.savings_rate,
                current=current.savings_rate,
                absolute_change=quantize_percentage(sav_rate_delta),
                percentage_change=sav_rate_delta,
                severity=sev,
                source="financial_engine",
                description=desc,
            )
        )

    # 8. Budget Variance & Overspending
    if current.budget_variance < Decimal("0.00") and abs(current.budget_variance) >= Decimal("50.00"):
        sev = "critical" if abs(current.budget_variance) >= Decimal("300.00") else "high"
        desc = f"Budget overspending detected: Outflows exceed configured limits by ${abs(current.budget_variance):,.2f}."
        changes.append(
            FinancialChangeItem(
                metric="budget_variance",
                baseline=baseline.budget_variance,
                current=current.budget_variance,
                absolute_change=quantize_currency(current.budget_variance),
                percentage_change=Decimal("0.00"),
                severity=sev,
                source="financial_engine",
                description=desc,
            )
        )

    # 9. Goal Portfolio Feasibility & Shortfall
    if (not current.goals_feasible and baseline.goals_feasible) or (current.goals_monthly_required > current.goals_monthly_capacity and current.active_goals_count > 0):
        shortfall = max(Decimal("0.00"), current.goals_monthly_required - current.goals_monthly_capacity)
        sev = "critical" if shortfall > Decimal("500.00") else "high"
        desc = (
            f"Goal funding conflict: Required monthly contributions (${current.goals_monthly_required:,.2f}) "
            f"exceed available savings capacity (${current.goals_monthly_capacity:,.2f}) by ${shortfall:,.2f}/month."
        )
        changes.append(
            FinancialChangeItem(
                metric="goal_contribution",
                baseline=baseline.goals_monthly_required,
                current=current.goals_monthly_required,
                absolute_change=quantize_currency(shortfall),
                percentage_change=Decimal("0.00"),
                severity=sev,
                source="financial_engine",
                description=desc,
            )
        )

    # 10. Financial Health Score Change
    health_delta = current.financial_health_score - baseline.financial_health_score
    if abs(health_delta) >= Decimal("3.00"):
        sev = "high" if health_delta <= Decimal("-10.00") else "medium" if health_delta < Decimal("0.00") else "low"
        desc = (
            f"Financial health score dropped from {baseline.financial_health_score} ({baseline.financial_health_grade}) to {current.financial_health_score} ({current.financial_health_grade})."
            if health_delta < 0
            else f"Financial health score improved from {baseline.financial_health_score} to {current.financial_health_score}."
        )
        changes.append(
            FinancialChangeItem(
                metric="financial_health",
                baseline=baseline.financial_health_score,
                current=current.financial_health_score,
                absolute_change=quantize_currency(health_delta),
                percentage_change=health_delta,
                severity=sev,
                source="financial_engine",
                description=desc,
            )
        )

    return changes


def evaluate_replanning_triggers(
    changes: List[FinancialChangeItem],
    current: MonitoringSnapshot,
    baseline: MonitoringSnapshot,
) -> ReplanningAssessment:
    """
    Deterministic replanning decision layer:
    Evaluates whether financial deviations warrant an updated plan.
    """
    critical_changes = [c for c in changes if c.severity == "critical"]
    high_changes = [c for c in changes if c.severity == "high"]

    reasons: List[str] = []
    affected_areas: List[str] = []
    triggers: List[str] = []

    # Check Trigger 1: Income decrease
    income_change = next((c for c in changes if c.metric == "income" and c.absolute_change < 0), None)
    if income_change and (income_change.severity in ["critical", "high"] or abs(income_change.percentage_change) >= Decimal("10.00")):
        triggers.append("income_change")
        affected_areas.extend(["income", "savings", "goals", "safe_to_spend"])
        reasons.append(f"Net monthly income decreased by ${abs(income_change.absolute_change):,.2f} ({abs(income_change.percentage_change)}%).")

    # Check Trigger 2: Safe to spend depleted
    if current.safe_to_spend_daily <= Decimal("0.00"):
        triggers.append("safe_to_spend_depleted")
        affected_areas.extend(["safe_to_spend", "cash_flow"])
        reasons.append(f"Daily safe-to-spend reached $0.00/day due to encumbered cash flow obligations.")

    # Check Trigger 3: Emergency Runway Depletion
    if current.emergency_runway_months < Decimal("3.00") and (baseline.emergency_runway_months >= Decimal("3.00") or current.emergency_runway_months < baseline.emergency_runway_months):
        triggers.append("emergency_runway_depleted")
        affected_areas.extend(["emergency_fund", "savings"])
        reasons.append(f"Emergency runway fell to {current.emergency_runway_months} months (below recommended 3.0 months).")

    # Check Trigger 4: Goal Infeasibility
    if not current.goals_feasible or (current.goals_monthly_required > current.goals_monthly_capacity and current.active_goals_count > 0):
        triggers.append("goal_infeasible")
        affected_areas.extend(["goals", "savings"])
        reasons.append(f"Goal funding shortfall of ${abs(current.goals_monthly_required - current.goals_monthly_capacity):,.2f}/month detected.")

    # Check Trigger 5: Recurring Commitments surge
    rec_change = next((c for c in changes if c.metric == "recurring_commitments" and c.absolute_change > 0), None)
    if rec_change and (rec_change.severity in ["critical", "high"] or rec_change.absolute_change >= Decimal("200.00")):
        triggers.append("recurring_outflow_surge")
        affected_areas.extend(["recurring_commitments", "cash_flow", "safe_to_spend"])
        reasons.append(f"Recurring monthly commitments increased by ${rec_change.absolute_change:,.2f}/month.")

    # Check Trigger 6: Spending Surge (Discretionary / Essential)
    disc_change = next((c for c in changes if c.metric == "discretionary_expenses" and c.absolute_change > 0), None)
    if disc_change and disc_change.severity in ["critical", "high"]:
        triggers.append("spending_surge")
        affected_areas.extend(["discretionary_expenses", "budget", "savings"])
        reasons.append(f"Discretionary spending surged by ${disc_change.absolute_change:,.2f} (+{disc_change.percentage_change}%).")

    # Check Trigger 7: Budget Overrun
    if current.budget_variance < Decimal("-100.00"):
        triggers.append("budget_overrun")
        affected_areas.extend(["budget", "cash_flow"])
        reasons.append(f"Budget exceeded by ${abs(current.budget_variance):,.2f}.")

    # Deduplicate affected areas
    unique_areas = list(dict.fromkeys(affected_areas))

    if len(triggers) > 0:
        primary_trigger = triggers[0]
        sev = "critical" if len(critical_changes) > 0 or len(triggers) >= 3 else "high"
        recommendations = [
            "Reallocate monthly salary to protect essential commitments.",
            "Rebalance goal milestone timelines to prevent liquidity shortfall.",
            "Reduce discretionary spending allowance until emergency runway recovers.",
        ]
        return ReplanningAssessment(
            replanning_required=True,
            trigger=primary_trigger,
            severity=sev,
            affected_areas=unique_areas,
            reasons=reasons,
            recommendations=recommendations,
        )
    else:
        return ReplanningAssessment(
            replanning_required=False,
            trigger="nominal",
            severity="low",
            affected_areas=[],
            reasons=["All monitored metrics remain within safe operating thresholds. Existing financial plan is fully viable."],
            recommendations=["Continue executing current salary allocation and goal milestones as planned."],
        )


def generate_adaptive_replanning_strategies(
    current: MonitoringSnapshot,
    baseline: MonitoringSnapshot,
    active_goals: Optional[List[Dict[str, Any]]] = None,
) -> List[ReplanningStrategyOption]:
    """
    Deterministic strategy generator when replanning is required:
    Produces 4 transparent alternatives to resolve financial imbalances.
    """
    income = current.monthly_income
    fixed = current.recurring_commitments_monthly
    essential = current.monthly_essential_expenses
    
    # Available surplus for flexible allocation
    surplus = max(Decimal("0.00"), income - fixed - essential)

    strategies: List[ReplanningStrategyOption] = []

    # Strategy 1: Prioritize Goals & Emergency Runway (Aggressive Discretionary Cut)
    s1_savings = min(surplus, current.goals_monthly_required if current.goals_monthly_required > 0 else quantize_currency(income * Decimal("0.25")))
    s1_disc = max(Decimal("0.00"), surplus - s1_savings)
    s1_buf = max(Decimal("0.00"), surplus - s1_savings - s1_disc)
    strategies.append(
        ReplanningStrategyOption(
            strategy_id="strategy_protect_goals",
            title="Strategy A: Protect Goals & Fast Runway Recovery",
            description=f"Maintain goal funding at ${s1_savings:,.2f}/mo by tightening discretionary spending to ${s1_disc:,.2f}/mo.",
            adjusted_essential=essential,
            adjusted_savings=s1_savings,
            adjusted_discretionary=s1_disc,
            resulting_buffer=s1_buf,
            impact_on_goals="Preserves active goal completion timelines without delay.",
            tradeoffs=[
                f"Requires reducing monthly lifestyle/discretionary spending to ${s1_disc:,.2f}.",
                f"Maximizes speed of emergency fund replenishment to {quantize_currency(current.emergency_runway_months + Decimal('0.5'))} months.",
            ],
        )
    )

    # Strategy 2: Balanced Compromise (60% Savings / 40% Discretionary)
    s2_savings = quantize_currency(surplus * Decimal("0.60"))
    s2_disc = quantize_currency(surplus * Decimal("0.40"))
    s2_buf = max(Decimal("0.00"), surplus - s2_savings - s2_disc)
    strategies.append(
        ReplanningStrategyOption(
            strategy_id="strategy_balanced",
            title="Strategy B: Balanced Adaptation",
            description=f"Distribute monthly surplus 60% to savings/goals (${s2_savings:,.2f}) and 40% to discretionary (${s2_disc:,.2f}).",
            adjusted_essential=essential,
            adjusted_savings=s2_savings,
            adjusted_discretionary=s2_disc,
            resulting_buffer=s2_buf,
            impact_on_goals="Minor timeline extension (1-3 months) for lower-priority goals.",
            tradeoffs=[
                "Maintains reasonable daily spending comfort while keeping savings positive.",
                "Non-urgent goals are slightly delayed to avoid cash flow stress.",
            ],
        )
    )

    # Strategy 3: Lifestyle Protection (Protect Discretionary, Extend Goal Timelines)
    s3_disc = min(surplus, quantize_currency(income * Decimal("0.20")))
    s3_savings = max(Decimal("0.00"), surplus - s3_disc)
    s3_buf = max(Decimal("0.00"), surplus - s3_savings - s3_disc)
    strategies.append(
        ReplanningStrategyOption(
            strategy_id="strategy_protect_lifestyle",
            title="Strategy C: Lifestyle Protection & Timeline Extension",
            description=f"Keep discretionary spending at ${s3_disc:,.2f}/mo and rebalance savings to ${s3_savings:,.2f}/mo.",
            adjusted_essential=essential,
            adjusted_savings=s3_savings,
            adjusted_discretionary=s3_disc,
            resulting_buffer=s3_buf,
            impact_on_goals="Extends goal milestones across the board to match the reduced monthly savings contribution.",
            tradeoffs=[
                "Minimizes lifestyle shock during income or expense transition.",
                "Requires pushing target goal deadlines further into the future.",
            ],
        )
    )

    # Strategy 4: High Buffer / Defensive Mode (Max Cash Reserve)
    s4_savings = quantize_currency(surplus * Decimal("0.40"))
    s4_disc = quantize_currency(surplus * Decimal("0.30"))
    s4_buf = max(Decimal("0.00"), surplus - s4_savings - s4_disc)
    strategies.append(
        ReplanningStrategyOption(
            strategy_id="strategy_defensive_buffer",
            title="Strategy D: Defensive Cash Buffer",
            description=f"Allocate ${s4_buf:,.2f}/mo directly into an unallocated cash buffer to absorb further volatility.",
            adjusted_essential=essential,
            adjusted_savings=s4_savings,
            adjusted_discretionary=s4_disc,
            resulting_buffer=s4_buf,
            impact_on_goals="Lower monthly goal contribution until financial stability is confirmed.",
            tradeoffs=[
                f"Creates a safety buffer of ${s4_buf:,.2f}/month against unexpected expenses.",
                "Slows progress on long-term wealth milestones in exchange for immediate security.",
            ],
        )
    )

    return strategies


def generate_plan_comparison(
    baseline: MonitoringSnapshot,
    proposed_strategy: ReplanningStrategyOption,
    reason: str = "Financial change detected by monitoring engine",
    active_goals: Optional[List[Dict[str, Any]]] = None,
) -> PlanComparisonTable:
    """
    Constructs a structured Before vs. After comparison table.
    """
    items: List[PlanComparisonItem] = []

    # 1. Monthly Income
    inc_delta = proposed_strategy.adjusted_essential + proposed_strategy.adjusted_savings + proposed_strategy.adjusted_discretionary + proposed_strategy.resulting_buffer - baseline.monthly_income
    items.append(
        PlanComparisonItem(
            area="income",
            metric="Net Monthly Income",
            baseline_value=f"${baseline.monthly_income:,.2f}",
            proposed_value=f"${baseline.monthly_income:,.2f}",
            delta="$0.00",
            explanation="Baseline verified net income.",
        )
    )

    # 2. Fixed Commitments
    items.append(
        PlanComparisonItem(
            area="commitments",
            metric="Fixed Commitments",
            baseline_value=f"${baseline.recurring_commitments_monthly:,.2f}/mo",
            proposed_value=f"${baseline.recurring_commitments_monthly:,.2f}/mo",
            delta="$0.00",
            explanation="Committed bills, loans, and subscriptions.",
        )
    )

    # 3. Essential Allowance
    ess_delta = proposed_strategy.adjusted_essential - baseline.monthly_essential_expenses
    items.append(
        PlanComparisonItem(
            area="essentials",
            metric="Essential Living Allowance",
            baseline_value=f"${baseline.monthly_essential_expenses:,.2f}/mo",
            proposed_value=f"${proposed_strategy.adjusted_essential:,.2f}/mo",
            delta=f"{'+' if ess_delta >= 0 else ''}${ess_delta:,.2f}",
            explanation="Groceries, utilities, health, and transit essentials.",
        )
    )

    # 4. Savings Allocation
    baseline_savings = max(Decimal("0.00"), baseline.monthly_income - baseline.monthly_essential_expenses - baseline.monthly_discretionary_expenses - baseline.recurring_commitments_monthly)
    sav_delta = proposed_strategy.adjusted_savings - baseline_savings
    items.append(
        PlanComparisonItem(
            area="savings",
            metric="Monthly Savings & Goals Allocation",
            baseline_value=f"${baseline_savings:,.2f}/mo",
            proposed_value=f"${proposed_strategy.adjusted_savings:,.2f}/mo",
            delta=f"{'+' if sav_delta >= 0 else ''}${sav_delta:,.2f}",
            explanation="Dedicated monthly capital for emergency reserve and active goals.",
        )
    )

    # 5. Discretionary Spending Allowance
    disc_delta = proposed_strategy.adjusted_discretionary - baseline.monthly_discretionary_expenses
    items.append(
        PlanComparisonItem(
            area="discretionary",
            metric="Discretionary Spending Allowance",
            baseline_value=f"${baseline.monthly_discretionary_expenses:,.2f}/mo",
            proposed_value=f"${proposed_strategy.adjusted_discretionary:,.2f}/mo",
            delta=f"{'+' if disc_delta >= 0 else ''}${disc_delta:,.2f}",
            explanation="Flexible dining, shopping, and entertainment allowance.",
        )
    )

    # 6. Safety Buffer
    items.append(
        PlanComparisonItem(
            area="buffer",
            metric="Unallocated Safety Buffer",
            baseline_value="$0.00/mo",
            proposed_value=f"${proposed_strategy.resulting_buffer:,.2f}/mo",
            delta=f"+${proposed_strategy.resulting_buffer:,.2f}",
            explanation="Cash buffer to absorb mid-month spending volatility.",
        )
    )

    # 7. Daily Safe-to-Spend
    new_safe_daily = quantize_currency(proposed_strategy.adjusted_discretionary / Decimal("30.00"))
    safe_delta = new_safe_daily - baseline.safe_to_spend_daily
    items.append(
        PlanComparisonItem(
            area="safe_to_spend",
            metric="Daily Safe-to-Spend Limit",
            baseline_value=f"${baseline.safe_to_spend_daily:,.2f}/day",
            proposed_value=f"${new_safe_daily:,.2f}/day",
            delta=f"{'+' if safe_delta >= 0 else ''}${safe_delta:,.2f}/day",
            explanation="Recommended daily spending cap to remain on track.",
        )
    )

    # Affected goals list
    affected_goals_data: List[Dict[str, Any]] = []
    if active_goals:
        for g in active_goals:
            g_name = g.get("name", "Goal")
            g_target = to_decimal(g.get("target_amount", 0))
            g_curr = to_decimal(g.get("current_amount", 0))
            g_prev_contrib = to_decimal(g.get("monthly_contribution", 0))

            # Scale contribution according to new savings allocation
            scale = safe_divide(proposed_strategy.adjusted_savings, baseline_savings) if baseline_savings > 0 else Decimal("1.00")
            g_new_contrib = quantize_currency(g_prev_contrib * scale)
            rem = max(Decimal("0.00"), g_target - g_curr)
            prev_months = int((rem / g_prev_contrib).quantize(Decimal("1"))) if g_prev_contrib > 0 else 999
            new_months = int((rem / g_new_contrib).quantize(Decimal("1"))) if g_new_contrib > 0 else 999
            delay = new_months - prev_months if (new_months < 999 and prev_months < 999) else 0

            affected_goals_data.append({
                "goal_name": g_name,
                "previous_contribution": str(g_prev_contrib),
                "proposed_contribution": str(g_new_contrib),
                "timeline_delay_months": delay if delay > 0 else 0,
                "status": "on_track" if delay <= 0 else "delayed",
            })

    summary = (
        f"Proposed adaptation adjusts monthly savings to ${proposed_strategy.adjusted_savings:,.2f} "
        f"and discretionary spending to ${proposed_strategy.adjusted_discretionary:,.2f} "
        f"to address: {reason}."
    )

    return PlanComparisonTable(
        items=items,
        summary=summary,
        affected_goals=affected_goals_data,
    )
