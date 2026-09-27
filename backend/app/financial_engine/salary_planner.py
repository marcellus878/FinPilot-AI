import calendar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.financial_engine.helpers import quantize_currency, quantize_percentage, safe_divide, to_decimal


@dataclass
class SalaryCycleDates:
    cycle_start_date: datetime
    next_salary_date: datetime
    days_in_cycle: int
    days_elapsed: int
    days_remaining: int


@dataclass
class RecurringCommitmentItem:
    id: str
    name: str
    category: str
    amount: Decimal
    frequency: str  # 'weekly' | 'monthly' | 'quarterly' | 'annual'
    monthly_equivalent: Decimal
    next_expected_date: Optional[datetime]
    is_active: bool
    is_confirmed: bool
    is_due_in_current_cycle: bool


@dataclass
class AllocationAlternative:
    title: str
    description: str
    adjusted_savings_target: Decimal
    adjusted_essential_allowance: Decimal
    adjusted_discretionary_allowance: Decimal
    resulting_buffer: Decimal


@dataclass
class SalaryAllocationResult:
    monthly_income: Decimal
    fixed_commitments: Decimal
    essential_allowance: Decimal
    savings_target: Decimal
    discretionary_allowance: Decimal
    remaining_buffer: Decimal
    fixed_percentage: Decimal
    essential_percentage: Decimal
    savings_percentage: Decimal
    discretionary_percentage: Decimal
    buffer_percentage: Decimal
    is_feasible: bool
    deficit_amount: Decimal
    explanation: str
    alternatives: List[AllocationAlternative] = field(default_factory=list)


@dataclass
class SafeToSpendResult:
    current_available_funds: Decimal
    upcoming_commitments: Decimal
    remaining_essential_allowance: Decimal
    savings_reserve: Decimal
    emergency_reserve: Decimal
    total_committed_and_reserved: Decimal
    safe_to_spend_amount: Decimal
    daily_safe_to_spend: Decimal
    days_remaining: int
    explanation: str


@dataclass
class SurvivalProjectionResult:
    current_available_funds: Decimal
    recent_average_daily_burn: Decimal
    days_remaining: int
    upcoming_commitments: Decimal
    projected_remaining_spend: Decimal
    projected_end_of_month_balance: Decimal
    daily_spending_capacity: Decimal
    status: str  # 'comfortable' | 'watch' | 'at_risk' | 'insufficient_data'
    explanation: str
    evidence: Dict[str, Any] = field(default_factory=dict)


def calculate_salary_cycle_dates(
    expected_salary_day: int = 1,
    reference_date: Optional[datetime] = None,
) -> SalaryCycleDates:
    """
    Computes the current pay-cycle start date, next expected salary date,
    days elapsed, and days remaining.
    """
    if not reference_date:
        reference_date = datetime.now()

    # Normalize expected day (clamp between 1 and 28-31 depending on month)
    ref_year = reference_date.year
    ref_month = reference_date.month
    ref_day = reference_date.day

    max_days_current_month = calendar.monthrange(ref_year, ref_month)[1]
    clamped_salary_day = min(max(1, expected_salary_day), max_days_current_month)

    # Determine if salary has already arrived this month or is coming up
    if ref_day >= clamped_salary_day:
        # Salary arrived this month; cycle start is this month's salary day
        cycle_start = datetime(ref_year, ref_month, clamped_salary_day, 0, 0, 0)
        # Next salary is next month
        if ref_month == 12:
            next_year, next_month = ref_year + 1, 1
        else:
            next_year, next_month = ref_year, ref_month + 1

        max_days_next_month = calendar.monthrange(next_year, next_month)[1]
        next_salary_day = min(clamped_salary_day, max_days_next_month)
        next_salary = datetime(next_year, next_month, next_salary_day, 0, 0, 0)
    else:
        # Salary has not arrived this month; cycle start was previous month
        if ref_month == 1:
            prev_year, prev_month = ref_year - 1, 12
        else:
            prev_year, prev_month = ref_year, ref_month - 1

        max_days_prev_month = calendar.monthrange(prev_year, prev_month)[1]
        prev_salary_day = min(clamped_salary_day, max_days_prev_month)
        cycle_start = datetime(prev_year, prev_month, prev_salary_day, 0, 0, 0)
        next_salary = datetime(ref_year, ref_month, clamped_salary_day, 0, 0, 0)

    total_days = max(1, (next_salary.date() - cycle_start.date()).days)
    days_elapsed = max(0, (reference_date.date() - cycle_start.date()).days)
    days_remaining = max(1, (next_salary.date() - reference_date.date()).days)

    return SalaryCycleDates(
        cycle_start_date=cycle_start,
        next_salary_date=next_salary,
        days_in_cycle=total_days,
        days_elapsed=days_elapsed,
        days_remaining=days_remaining,
    )


def normalize_commitment_to_monthly(amount: Decimal, frequency: str) -> Decimal:
    """
    Converts amounts from weekly/quarterly/annual cadences to monthly equivalent.
    """
    amt = to_decimal(amount)
    freq = (frequency or "monthly").lower().strip()

    if freq == "weekly":
        # 52 weeks / 12 months = 4.3333 weeks/month
        return quantize_currency(amt * Decimal("4.3333333333"))
    elif freq == "quarterly":
        return quantize_currency(amt / Decimal("3.00"))
    elif freq == "annual" or freq == "yearly":
        return quantize_currency(amt / Decimal("12.00"))
    return quantize_currency(amt)


def calculate_monthly_recurring_commitments(
    commitments: List[Any],
    next_salary_date: datetime,
    reference_date: Optional[datetime] = None,
) -> Tuple[List[RecurringCommitmentItem], Decimal, Decimal]:
    """
    Processes confirmed commitments, calculating:
    - Normalized items list
    - Total monthly recurring commitments
    - Upcoming commitments due before the next salary date
    """
    if not reference_date:
        reference_date = datetime.now()

    items: List[RecurringCommitmentItem] = []
    total_monthly = Decimal("0.00")
    upcoming_due = Decimal("0.00")

    for c in commitments:
        if isinstance(c, dict):
            c_id = str(c.get("id") or c.get("name") or "comm")
            name = str(c.get("name") or c.get("merchant") or "Commitment")
            cat = str(c.get("category") or "Bills & Utilities")
            raw_amt = to_decimal(c.get("amount") or c.get("approximate_amount") or 0)
            freq = str(c.get("frequency") or "monthly")
            is_active = bool(c.get("is_active", True))
            is_confirmed = bool(c.get("is_confirmed", True))
            next_exp = c.get("next_expected_date")
        else:
            c_id = str(getattr(c, "id", getattr(c, "name", "comm")))
            name = str(getattr(c, "name", getattr(c, "merchant", "Commitment")))
            cat = str(getattr(c, "category", "Bills & Utilities"))
            raw_amt = to_decimal(getattr(c, "amount", getattr(c, "approximate_amount", 0)))
            freq = str(getattr(c, "frequency", "monthly"))
            is_active = bool(getattr(c, "is_active", True))
            is_confirmed = bool(getattr(c, "is_confirmed", True))
            next_exp = getattr(c, "next_expected_date", None)

        if not is_active or raw_amt <= Decimal("0.00"):
            continue

        monthly_amt = normalize_commitment_to_monthly(raw_amt, freq)
        total_monthly += monthly_amt

        # Check if due before next salary date
        is_due = True
        if next_exp:
            if isinstance(next_exp, str):
                try:
                    next_exp = datetime.fromisoformat(next_exp)
                except ValueError:
                    next_exp = None
            if next_exp and (next_exp > next_salary_date or next_exp < reference_date):
                is_due = False

        if is_due:
            upcoming_due += monthly_amt

        items.append(
            RecurringCommitmentItem(
                id=c_id,
                name=name,
                category=cat,
                amount=raw_amt,
                frequency=freq,
                monthly_equivalent=monthly_amt,
                next_expected_date=next_exp if isinstance(next_exp, datetime) else None,
                is_active=is_active,
                is_confirmed=is_confirmed,
                is_due_in_current_cycle=is_due,
            )
        )

    return items, quantize_currency(total_monthly), quantize_currency(upcoming_due)


def calculate_salary_allocation(
    monthly_income: Decimal,
    fixed_commitments: Decimal,
    essential_allowance: Optional[Decimal] = None,
    savings_target: Optional[Decimal] = None,
    discretionary_allowance: Optional[Decimal] = None,
) -> SalaryAllocationResult:
    """
    Deterministic Salary Allocation Engine.
    Allocates available income into Fixed, Essential, Savings, Discretionary, and Buffer.
    Detects infeasible allocations and generates transparent rebalancing alternatives.
    """
    income = to_decimal(monthly_income)
    fixed = to_decimal(fixed_commitments)

    # Defaults if not explicitly configured
    # 50/30/20 standard baseline adapted to fixed commitments:
    # 1. Fixed commitments take first priority
    # 2. Essentials default to ~25% or remaining essential needs
    # 3. Savings default to 20%
    # 4. Discretionary defaults to 15%
    if essential_allowance is None:
        essential_allowance = quantize_currency(income * Decimal("0.25"))
    else:
        essential_allowance = to_decimal(essential_allowance)

    if savings_target is None:
        savings_target = quantize_currency(income * Decimal("0.20"))
    else:
        savings_target = to_decimal(savings_target)

    if discretionary_allowance is None:
        discretionary_allowance = quantize_currency(income * Decimal("0.15"))
    else:
        discretionary_allowance = to_decimal(discretionary_allowance)

    total_allocated = fixed + essential_allowance + savings_target + discretionary_allowance
    buffer = income - total_allocated

    is_feasible = buffer >= Decimal("0.00")
    deficit = quantize_currency(abs(buffer)) if not is_feasible else Decimal("0.00")
    remaining_buffer = quantize_currency(max(Decimal("0.00"), buffer))

    fixed_pct = quantize_percentage(safe_divide(fixed, income) * Decimal("100.00"))
    ess_pct = quantize_percentage(safe_divide(essential_allowance, income) * Decimal("100.00"))
    sav_pct = quantize_percentage(safe_divide(savings_target, income) * Decimal("100.00"))
    disc_pct = quantize_percentage(safe_divide(discretionary_allowance, income) * Decimal("100.00"))
    buf_pct = quantize_percentage(safe_divide(remaining_buffer, income) * Decimal("100.00"))

    alternatives: List[AllocationAlternative] = []

    if not is_feasible:
        explanation = (
            f"Requested allocations exceed total monthly income by ${deficit:,.2f}. "
            f"Fixed commitments (${fixed:,.2f}) and essential allowance (${essential_allowance:,.2f}) "
            f"leave insufficient headroom for the combined savings (${savings_target:,.2f}) and discretionary target (${discretionary_allowance:,.2f})."
        )

        # Alternative 1: Prioritize Savings, reduce Discretionary
        avail_after_fixed_ess_sav = income - fixed - essential_allowance - savings_target
        alt1_disc = max(Decimal("0.00"), avail_after_fixed_ess_sav)
        alt1_sav = savings_target
        alt1_buf = max(Decimal("0.00"), income - (fixed + essential_allowance + alt1_sav + alt1_disc))
        alternatives.append(
            AllocationAlternative(
                title="Priority: Maintain Savings Target",
                description=f"Keep full savings target of ${alt1_sav:,.2f} by adjusting discretionary allowance to ${alt1_disc:,.2f}.",
                adjusted_savings_target=alt1_sav,
                adjusted_essential_allowance=essential_allowance,
                adjusted_discretionary_allowance=alt1_disc,
                resulting_buffer=alt1_buf,
            )
        )

        # Alternative 2: Balanced Compromise (Share reduction between Savings and Discretionary)
        avail_for_flex = max(Decimal("0.00"), income - fixed - essential_allowance)
        alt2_sav = quantize_currency(avail_for_flex * Decimal("0.60"))
        alt2_disc = quantize_currency(avail_for_flex * Decimal("0.40"))
        alt2_buf = max(Decimal("0.00"), income - (fixed + essential_allowance + alt2_sav + alt2_disc))
        alternatives.append(
            AllocationAlternative(
                title="Balanced Allocation",
                description=f"Distribute flexible income: 60% to Savings (${alt2_sav:,.2f}) and 40% to Discretionary (${alt2_disc:,.2f}).",
                adjusted_savings_target=alt2_sav,
                adjusted_essential_allowance=essential_allowance,
                adjusted_discretionary_allowance=alt2_disc,
                resulting_buffer=alt2_buf,
            )
        )

        # Alternative 3: Lifestyle Protection (Protect Discretionary, reduce Savings)
        avail_after_fixed_ess_disc = income - fixed - essential_allowance - discretionary_allowance
        alt3_sav = max(Decimal("0.00"), avail_after_fixed_ess_disc)
        alt3_disc = discretionary_allowance
        alt3_buf = max(Decimal("0.00"), income - (fixed + essential_allowance + alt3_sav + alt3_disc))
        alternatives.append(
            AllocationAlternative(
                title="Priority: Protect Discretionary Allowance",
                description=f"Maintain discretionary target of ${alt3_disc:,.2f} by lowering savings target to ${alt3_sav:,.2f}.",
                adjusted_savings_target=alt3_sav,
                adjusted_essential_allowance=essential_allowance,
                adjusted_discretionary_allowance=alt3_disc,
                resulting_buffer=alt3_buf,
            )
        )
    else:
        explanation = (
            f"Allocation is fully feasible with a safety buffer of ${remaining_buffer:,.2f} ({buf_pct}% of income). "
            f"All fixed commitments, essential allowances, and savings goals are supported."
        )

    return SalaryAllocationResult(
        monthly_income=income,
        fixed_commitments=fixed,
        essential_allowance=essential_allowance,
        savings_target=savings_target,
        discretionary_allowance=discretionary_allowance,
        remaining_buffer=remaining_buffer,
        fixed_percentage=fixed_pct,
        essential_percentage=ess_pct,
        savings_percentage=sav_pct,
        discretionary_percentage=disc_pct,
        buffer_percentage=buf_pct,
        is_feasible=is_feasible,
        deficit_amount=deficit,
        explanation=explanation,
        alternatives=alternatives,
    )


def calculate_safe_to_spend(
    current_available_funds: Decimal,
    upcoming_commitments: Decimal,
    remaining_essential_allowance: Decimal,
    savings_reserve: Decimal,
    emergency_reserve: Decimal = Decimal("0.00"),
    days_remaining: int = 1,
) -> SafeToSpendResult:
    """
    Deterministic Safe-to-Spend Calculator.
    Calculates unencumbered spending money for the rest of the pay cycle.
    Formula:
    Safe to Spend = Available Funds - Upcoming Commitments - Remaining Essentials - Savings Reserve - Emergency Reserve
    """
    available = to_decimal(current_available_funds)
    commitments = to_decimal(upcoming_commitments)
    essentials = to_decimal(remaining_essential_allowance)
    savings = to_decimal(savings_reserve)
    emergency = to_decimal(emergency_reserve)
    days = max(1, days_remaining)

    total_encumbered = commitments + essentials + savings + emergency
    raw_safe = available - total_encumbered

    safe_amount = quantize_currency(max(Decimal("0.00"), raw_safe))
    daily_safe = quantize_currency(safe_amount / Decimal(str(days)))

    if raw_safe >= Decimal("0.00"):
        explanation = (
            f"You have ${safe_amount:,.2f} safe to spend (${daily_safe:,.2f}/day for {days} days) "
            f"after reserving ${commitments:,.2f} for upcoming commitments, "
            f"${essentials:,.2f} for essentials, and ${savings:,.2f} for savings."
        )
    else:
        deficit = quantize_currency(abs(raw_safe))
        explanation = (
            f"Safe to spend is $0.00. Current available funds are short by ${deficit:,.2f} "
            f"to cover upcoming fixed commitments (${commitments:,.2f}), essentials (${essentials:,.2f}), and savings (${savings:,.2f})."
        )

    return SafeToSpendResult(
        current_available_funds=available,
        upcoming_commitments=commitments,
        remaining_essential_allowance=essentials,
        savings_reserve=savings,
        emergency_reserve=emergency,
        total_committed_and_reserved=total_encumbered,
        safe_to_spend_amount=safe_amount,
        daily_safe_to_spend=daily_safe,
        days_remaining=days,
        explanation=explanation,
    )


def calculate_survival_projection(
    current_available_funds: Decimal,
    monthly_income: Decimal,
    recent_average_daily_burn: Decimal,
    days_remaining: int,
    upcoming_commitments: Decimal,
    remaining_essential_allowance: Decimal,
) -> SurvivalProjectionResult:
    """
    Deterministic End-of-Month Survival Predictor.
    Estimates whether funds will last until next expected salary date based on daily burn rate.
    """
    available = to_decimal(current_available_funds)
    income = to_decimal(monthly_income)
    burn_rate = to_decimal(recent_average_daily_burn)
    days = max(1, days_remaining)
    commitments = to_decimal(upcoming_commitments)
    essentials = to_decimal(remaining_essential_allowance)

    if available <= Decimal("0.00") and income <= Decimal("0.00"):
        return SurvivalProjectionResult(
            current_available_funds=Decimal("0.00"),
            recent_average_daily_burn=Decimal("0.00"),
            days_remaining=days,
            upcoming_commitments=commitments,
            projected_remaining_spend=Decimal("0.00"),
            projected_end_of_month_balance=Decimal("0.00"),
            daily_spending_capacity=Decimal("0.00"),
            status="insufficient_data",
            explanation="Insufficient income or balance data available to compute end-of-month cash-flow projection.",
        )

    # Projected spend for the remainder of the cycle
    projected_variable_spend = quantize_currency(burn_rate * Decimal(str(days)))
    total_projected_spend = quantize_currency(projected_variable_spend + commitments)

    projected_end_balance = quantize_currency(available - total_projected_spend)

    # Spending capacity per day to break even at 0 balance
    unencumbered_for_days = max(Decimal("0.00"), available - commitments)
    daily_capacity = quantize_currency(unencumbered_for_days / Decimal(str(days)))

    # Status classification thresholds
    comfort_threshold = quantize_currency(income * Decimal("0.15")) if income > 0 else Decimal("500.00")

    if projected_end_balance >= comfort_threshold:
        status = "comfortable"
        explanation = (
            f"Cash flow is comfortable. Projected end-of-month balance is ${projected_end_balance:,.2f} "
            f"at your current daily spend of ${burn_rate:,.2f}/day with {days} days remaining."
        )
    elif projected_end_balance >= Decimal("0.00"):
        status = "watch"
        explanation = (
            f"Cash flow is positive but tight. Projected end-of-month balance is ${projected_end_balance:,.2f}. "
            f"Maintain daily spending below ${daily_capacity:,.2f}/day to preserve positive cash flow."
        )
    else:
        status = "at_risk"
        deficit = abs(projected_end_balance)
        explanation = (
            f"Cash flow is at risk of shortfall by ${deficit:,.2f} before next salary date. "
            f"Your current daily spending of ${burn_rate:,.2f}/day exceeds safe daily capacity (${daily_capacity:,.2f}/day)."
        )

    return SurvivalProjectionResult(
        current_available_funds=available,
        recent_average_daily_burn=burn_rate,
        days_remaining=days,
        upcoming_commitments=commitments,
        projected_remaining_spend=total_projected_spend,
        projected_end_of_month_balance=projected_end_balance,
        daily_spending_capacity=daily_capacity,
        status=status,
        explanation=explanation,
        evidence={
            "days_remaining": days,
            "daily_burn_rate": str(burn_rate),
            "upcoming_commitments": str(commitments),
            "projected_variable_spend": str(projected_variable_spend),
            "comfort_threshold": str(comfort_threshold),
        },
    )
