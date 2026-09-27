import math
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from app.financial_engine.constants import (
    DECIMAL_ONE_HUNDRED,
    DECIMAL_ZERO,
    PRIORITY_RANKS,
)
from app.financial_engine.helpers import (
    quantize_currency,
    quantize_percentage,
    to_decimal,
)

@dataclass(frozen=True)
class GoalContributionResult:
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    months_remaining: int
    required_monthly_contribution: Decimal
    is_feasible: bool
    is_completed: bool
    status: str
    warning_or_error: Optional[str] = None

@dataclass(frozen=True)
class GoalTimelineResult:
    target_amount: Decimal
    current_amount: Decimal
    remaining_amount: Decimal
    monthly_contribution: Decimal
    months_to_complete: int
    is_achievable: bool
    is_completed: bool
    status: str

@dataclass(frozen=True)
class GoalAllocationItem:
    goal_id: str
    goal_name: str
    priority: str
    target_amount: Decimal
    current_amount: Decimal
    monthly_target_contribution: Decimal
    allocated_amount: Decimal
    is_fully_funded: bool
    shortfall: Decimal

@dataclass(frozen=True)
class GoalConflictAllocationResult:
    total_available_funds: Decimal
    total_allocated: Decimal
    remaining_unallocated: Decimal
    allocations: List[GoalAllocationItem]
    fully_funded_count: int
    partially_funded_count: int
    unfunded_count: int

def calculate_required_goal_contribution(
    target_amount: Union[int, float, str, Decimal],
    current_amount: Union[int, float, str, Decimal],
    target_date: Union[date, datetime, str],
    current_date: Optional[Union[date, datetime]] = None,
    monthly_disposable_income: Optional[Union[int, float, str, Decimal]] = None,
) -> GoalContributionResult:
    target = quantize_currency(to_decimal(target_amount, allow_negative=False, name="target_amount"))
    current = quantize_currency(to_decimal(current_amount, allow_negative=False, name="current_amount"))

    if current >= target:
        return GoalContributionResult(
            target_amount=target,
            current_amount=current,
            remaining_amount=DECIMAL_ZERO,
            months_remaining=0,
            required_monthly_contribution=DECIMAL_ZERO,
            is_feasible=True,
            is_completed=True,
            status="completed",
            warning_or_error=None,
        )

    remaining = quantize_currency(target - current)

    if isinstance(target_date, str):
        target_d = datetime.strptime(target_date, "%Y-%m-%d").date()
    elif isinstance(target_date, datetime):
        target_d = target_date.date()
    else:
        target_d = target_date

    if current_date is None:
        curr_d = date.today()
    elif isinstance(current_date, datetime):
        curr_d = current_date.date()
    else:
        curr_d = current_date

    year_diff = target_d.year - curr_d.year
    month_diff = target_d.month - curr_d.month
    day_diff = target_d.day - curr_d.day

    total_months = year_diff * 12 + month_diff
    if day_diff > 15:
        total_months += 1

    if total_months <= 0:
        return GoalContributionResult(
            target_amount=target,
            current_amount=current,
            remaining_amount=remaining,
            months_remaining=0,
            required_monthly_contribution=remaining,
            is_feasible=False,
            is_completed=False,
            status="unfeasible_deadline",
            warning_or_error="Target date is in the past or less than 1 month away.",
        )

    months_dec = Decimal(str(total_months))
    req_monthly = quantize_currency(remaining / months_dec)

    is_feasible = True
    status = "feasible"
    warning = None

    if monthly_disposable_income is not None:
        disp = to_decimal(monthly_disposable_income, allow_negative=True, name="monthly_disposable_income")
        if req_monthly > disp:
            is_feasible = False
            status = "underfunded"
            warning = f"Required monthly contribution (${req_monthly}) exceeds monthly disposable income (${disp})."

    return GoalContributionResult(
        target_amount=target,
        current_amount=current,
        remaining_amount=remaining,
        months_remaining=total_months,
        required_monthly_contribution=req_monthly,
        is_feasible=is_feasible,
        is_completed=False,
        status=status,
        warning_or_error=warning,
    )

def calculate_goal_completion_timeline(
    target_amount: Union[int, float, str, Decimal],
    current_amount: Union[int, float, str, Decimal],
    monthly_contribution: Union[int, float, str, Decimal],
) -> GoalTimelineResult:
    target = quantize_currency(to_decimal(target_amount, allow_negative=False, name="target_amount"))
    current = quantize_currency(to_decimal(current_amount, allow_negative=False, name="current_amount"))
    contribution = quantize_currency(to_decimal(monthly_contribution, allow_negative=False, name="monthly_contribution"))

    if current >= target:
        return GoalTimelineResult(
            target_amount=target,
            current_amount=current,
            remaining_amount=DECIMAL_ZERO,
            monthly_contribution=contribution,
            months_to_complete=0,
            is_achievable=True,
            is_completed=True,
            status="completed",
        )

    remaining = quantize_currency(target - current)

    if contribution <= DECIMAL_ZERO:
        return GoalTimelineResult(
            target_amount=target,
            current_amount=current,
            remaining_amount=remaining,
            monthly_contribution=DECIMAL_ZERO,
            months_to_complete=-1,
            is_achievable=False,
            is_completed=False,
            status="unachievable_zero_contribution",
        )

    months_float = float(remaining / contribution)
    months = math.ceil(months_float)

    return GoalTimelineResult(
        target_amount=target,
        current_amount=current,
        remaining_amount=remaining,
        monthly_contribution=contribution,
        months_to_complete=months,
        is_achievable=True,
        is_completed=False,
        status="achievable",
    )

def allocate_goals_conflict(
    goals: List[Dict[str, Any]],
    available_monthly_funds: Union[int, float, str, Decimal],
    protect_mandatory: bool = True,
) -> GoalConflictAllocationResult:
    available = quantize_currency(to_decimal(available_monthly_funds, allow_negative=False, name="available_monthly_funds"))

    if not goals or available <= DECIMAL_ZERO:
        alloc_items = [
            GoalAllocationItem(
                goal_id=str(g.get("id", f"goal_{i}")),
                goal_name=str(g.get("name", f"Goal {i}")),
                priority=str(g.get("priority", "medium")).lower(),
                target_amount=quantize_currency(to_decimal(g.get("target_amount", DECIMAL_ZERO))),
                current_amount=quantize_currency(to_decimal(g.get("current_amount", DECIMAL_ZERO))),
                monthly_target_contribution=quantize_currency(to_decimal(g.get("required_monthly", DECIMAL_ZERO))),
                allocated_amount=DECIMAL_ZERO,
                is_fully_funded=False,
                shortfall=quantize_currency(to_decimal(g.get("required_monthly", DECIMAL_ZERO))),
            )
            for i, g in enumerate(goals)
        ]
        return GoalConflictAllocationResult(
            total_available_funds=available,
            total_allocated=DECIMAL_ZERO,
            remaining_unallocated=available,
            allocations=alloc_items,
            fully_funded_count=0,
            partially_funded_count=0,
            unfunded_count=len(goals),
        )

    priorities = ["high", "medium", "low"]
    grouped: Dict[str, List[Dict[str, Any]]] = {p: [] for p in priorities}

    for i, g in enumerate(goals):
        p = str(g.get("priority", "medium")).lower()
        if p not in grouped:
            p = "medium"
        req = quantize_currency(to_decimal(g.get("required_monthly", DECIMAL_ZERO), allow_negative=False))
        target = quantize_currency(to_decimal(g.get("target_amount", DECIMAL_ZERO), allow_negative=False))
        current = quantize_currency(to_decimal(g.get("current_amount", DECIMAL_ZERO), allow_negative=False))
        grouped[p].append({
            "id": str(g.get("id", f"goal_{i}")),
            "name": str(g.get("name", f"Goal {i}")),
            "priority": p,
            "target_amount": target,
            "current_amount": current,
            "required_monthly": req,
            "allocated": DECIMAL_ZERO,
        })

    remaining_funds = available

    for p in priorities:
        tier_goals = grouped[p]
        if not tier_goals or remaining_funds <= DECIMAL_ZERO:
            continue

        tier_total_req = sum(g["required_monthly"] for g in tier_goals)

        if remaining_funds >= tier_total_req:
            for g in tier_goals:
                g["allocated"] = g["required_monthly"]
            remaining_funds -= tier_total_req
        else:
            tier_allocated_sum = DECIMAL_ZERO
            for g in tier_goals:
                if tier_total_req > DECIMAL_ZERO:
                    portion = (g["required_monthly"] / tier_total_req) * remaining_funds
                    g["allocated"] = quantize_currency(portion)
                    tier_allocated_sum += g["allocated"]
                else:
                    g["allocated"] = DECIMAL_ZERO
            remaining_funds = max(DECIMAL_ZERO, remaining_funds - tier_allocated_sum)

    result_items: List[GoalAllocationItem] = []
    total_allocated = DECIMAL_ZERO
    fully_funded = 0
    partially_funded = 0
    unfunded = 0

    for p in priorities:
        for g in grouped[p]:
            alloc = g["allocated"]
            req = g["required_monthly"]
            shortfall = quantize_currency(max(DECIMAL_ZERO, req - alloc))
            is_full = (alloc >= req) and (req > DECIMAL_ZERO)

            if alloc >= req and req > DECIMAL_ZERO:
                fully_funded += 1
            elif alloc > DECIMAL_ZERO:
                partially_funded += 1
            else:
                unfunded += 1

            total_allocated += alloc
            result_items.append(
                GoalAllocationItem(
                    goal_id=g["id"],
                    goal_name=g["name"],
                    priority=g["priority"],
                    target_amount=g["target_amount"],
                    current_amount=g["current_amount"],
                    monthly_target_contribution=req,
                    allocated_amount=alloc,
                    is_fully_funded=is_full,
                    shortfall=shortfall,
                )
            )

    remaining_unalloc = quantize_currency(max(DECIMAL_ZERO, available - total_allocated))

    return GoalConflictAllocationResult(
        total_available_funds=available,
        total_allocated=quantize_currency(total_allocated),
        remaining_unallocated=remaining_unalloc,
        allocations=result_items,
        fully_funded_count=fully_funded,
        partially_funded_count=partially_funded,
        unfunded_count=unfunded,
    )


@dataclass(frozen=True)
class GoalConflictStrategy:
    strategy_id: str
    strategy_name: str
    description: str
    allocations: List[GoalAllocationItem]
    total_allocated: Decimal
    remaining_unallocated: Decimal
    fully_funded_count: int
    unfunded_count: int


@dataclass(frozen=True)
class GoalPortfolioAnalysisResult:
    total_target_amount: Decimal
    total_saved_amount: Decimal
    total_remaining_amount: Decimal
    overall_progress_percentage: Decimal
    total_required_monthly: Decimal
    available_monthly_capacity: Decimal
    net_monthly_surplus_or_shortfall: Decimal
    is_portfolio_feasible: bool
    conflict_detected: bool
    active_goals_count: int
    achieved_goals_count: int
    goal_evaluations: List[Dict[str, Any]]
    conflict_alternatives: List[GoalConflictStrategy]
    summary_explanation: str


def generate_goal_conflict_strategies(
    goals: List[Dict[str, Any]],
    available_monthly_funds: Union[int, float, str, Decimal],
) -> List[GoalConflictStrategy]:
    available = quantize_currency(to_decimal(available_monthly_funds, allow_negative=False, name="available_monthly_funds"))
    if not goals:
        return []

    active_goals = [g for g in goals if g.get("status") != "achieved"]
    if not active_goals:
        return []

    # 1. Strategy: Priority Waterfall (High -> Medium -> Low)
    waterfall_res = allocate_goals_conflict(active_goals, available)
    strategy_waterfall = GoalConflictStrategy(
        strategy_id="priority_waterfall",
        strategy_name="Priority Waterfall",
        description="Funds high-priority goals completely first, then allocates any remaining capacity to medium and low priority goals.",
        allocations=waterfall_res.allocations,
        total_allocated=waterfall_res.total_allocated,
        remaining_unallocated=waterfall_res.remaining_unallocated,
        fully_funded_count=waterfall_res.fully_funded_count,
        unfunded_count=waterfall_res.unfunded_count,
    )

    # 2. Strategy: Proportional Share
    total_req = sum(
        quantize_currency(to_decimal(g.get("required_monthly", DECIMAL_ZERO), allow_negative=False))
        for g in active_goals
    )

    prop_allocations: List[GoalAllocationItem] = []
    prop_total_alloc = DECIMAL_ZERO
    prop_fully_funded = 0
    prop_unfunded = 0

    for i, g in enumerate(active_goals):
        req = quantize_currency(to_decimal(g.get("required_monthly", DECIMAL_ZERO), allow_negative=False))
        target = quantize_currency(to_decimal(g.get("target_amount", DECIMAL_ZERO), allow_negative=False))
        curr = quantize_currency(to_decimal(g.get("current_amount", DECIMAL_ZERO), allow_negative=False))

        if total_req > DECIMAL_ZERO and available > DECIMAL_ZERO:
            alloc = quantize_currency((req / total_req) * available)
        else:
            alloc = DECIMAL_ZERO

        shortfall = quantize_currency(max(DECIMAL_ZERO, req - alloc))
        is_full = (alloc >= req) and (req > DECIMAL_ZERO)

        if is_full:
            prop_fully_funded += 1
        elif alloc <= DECIMAL_ZERO:
            prop_unfunded += 1

        prop_total_alloc += alloc
        prop_allocations.append(
            GoalAllocationItem(
                goal_id=str(g.get("id", f"goal_{i}")),
                goal_name=str(g.get("name", f"Goal {i}")),
                priority=str(g.get("priority", "medium")).lower(),
                target_amount=target,
                current_amount=curr,
                monthly_target_contribution=req,
                allocated_amount=alloc,
                is_fully_funded=is_full,
                shortfall=shortfall,
            )
        )

    strategy_proportional = GoalConflictStrategy(
        strategy_id="proportional_share",
        strategy_name="Proportional Progress",
        description="Distributes monthly savings proportionally so all goals make synchronized forward progress according to target size.",
        allocations=prop_allocations,
        total_allocated=quantize_currency(prop_total_alloc),
        remaining_unallocated=quantize_currency(max(DECIMAL_ZERO, available - prop_total_alloc)),
        fully_funded_count=prop_fully_funded,
        unfunded_count=prop_unfunded,
    )

    # 3. Strategy: Equal Split
    equal_allocations: List[GoalAllocationItem] = []
    equal_total_alloc = DECIMAL_ZERO
    equal_fully_funded = 0
    equal_unfunded = 0
    count = len(active_goals)
    per_goal_cap = quantize_currency(available / Decimal(str(count))) if count > 0 else DECIMAL_ZERO

    for i, g in enumerate(active_goals):
        req = quantize_currency(to_decimal(g.get("required_monthly", DECIMAL_ZERO), allow_negative=False))
        target = quantize_currency(to_decimal(g.get("target_amount", DECIMAL_ZERO), allow_negative=False))
        curr = quantize_currency(to_decimal(g.get("current_amount", DECIMAL_ZERO), allow_negative=False))

        alloc = min(req, per_goal_cap) if req > DECIMAL_ZERO else DECIMAL_ZERO
        shortfall = quantize_currency(max(DECIMAL_ZERO, req - alloc))
        is_full = (alloc >= req) and (req > DECIMAL_ZERO)

        if is_full:
            equal_fully_funded += 1
        elif alloc <= DECIMAL_ZERO:
            equal_unfunded += 1

        equal_total_alloc += alloc
        equal_allocations.append(
            GoalAllocationItem(
                goal_id=str(g.get("id", f"goal_{i}")),
                goal_name=str(g.get("name", f"Goal {i}")),
                priority=str(g.get("priority", "medium")).lower(),
                target_amount=target,
                current_amount=curr,
                monthly_target_contribution=req,
                allocated_amount=alloc,
                is_fully_funded=is_full,
                shortfall=shortfall,
            )
        )

    strategy_equal = GoalConflictStrategy(
        strategy_id="equal_split",
        strategy_name="Equal Split",
        description="Allocates an equal portion of monthly capacity across each goal for simple and balanced progress.",
        allocations=equal_allocations,
        total_allocated=quantize_currency(equal_total_alloc),
        remaining_unallocated=quantize_currency(max(DECIMAL_ZERO, available - equal_total_alloc)),
        fully_funded_count=equal_fully_funded,
        unfunded_count=equal_unfunded,
    )

    return [strategy_waterfall, strategy_proportional, strategy_equal]


def analyze_goal_portfolio(
    goals: List[Dict[str, Any]],
    available_monthly_capacity: Union[int, float, str, Decimal],
    reference_date: Optional[Union[date, datetime]] = None,
) -> GoalPortfolioAnalysisResult:
    capacity = quantize_currency(to_decimal(available_monthly_capacity, allow_negative=False, name="available_monthly_capacity"))
    ref_d = reference_date or date.today()
    if isinstance(ref_d, datetime):
        ref_d = ref_d.date()

    evaluations: List[Dict[str, Any]] = []
    total_target = DECIMAL_ZERO
    total_saved = DECIMAL_ZERO
    total_req_monthly = DECIMAL_ZERO
    active_count = 0
    achieved_count = 0

    for g in goals:
        target = quantize_currency(to_decimal(g.get("target_amount", DECIMAL_ZERO), allow_negative=False))
        curr = quantize_currency(to_decimal(g.get("current_amount", DECIMAL_ZERO), allow_negative=False))
        target_dt = g.get("target_date")
        user_contrib = g.get("monthly_contribution")
        status = str(g.get("status", "in_progress")).lower()

        rem = quantize_currency(max(DECIMAL_ZERO, target - curr))
        progress_pct = quantize_percentage((curr / target * DECIMAL_ONE_HUNDRED) if target > DECIMAL_ZERO else DECIMAL_ONE_HUNDRED)

        total_target += target
        total_saved += curr

        is_completed = (curr >= target) or (status == "achieved")
        if is_completed:
            achieved_count += 1
            status = "achieved"
        else:
            active_count += 1

        # Required contribution from target date
        req_contrib_res: Optional[GoalContributionResult] = None
        if target_dt and not is_completed:
            req_contrib_res = calculate_required_goal_contribution(
                target_amount=target,
                current_amount=curr,
                target_date=target_dt,
                current_date=ref_d,
                monthly_disposable_income=capacity,
            )
            req_monthly = req_contrib_res.required_monthly_contribution
            months_left = req_contrib_res.months_remaining
        else:
            req_monthly = quantize_currency(to_decimal(user_contrib or DECIMAL_ZERO, allow_negative=False))
            months_left = 0

        # Timeline projection
        effective_contrib = req_monthly
        if user_contrib is not None and to_decimal(user_contrib) > DECIMAL_ZERO:
            effective_contrib = quantize_currency(to_decimal(user_contrib))

        timeline_res = calculate_goal_completion_timeline(target, curr, effective_contrib)

        # Projected completion date
        projected_date_str: Optional[str] = None
        if timeline_res.is_achievable and timeline_res.months_to_complete > 0:
            proj_year = ref_d.year + (ref_d.month + timeline_res.months_to_complete - 1) // 12
            proj_month = ((ref_d.month + timeline_res.months_to_complete - 1) % 12) + 1
            proj_day = min(ref_d.day, 28)
            projected_date_str = date(proj_year, proj_month, proj_day).isoformat()
        elif is_completed:
            projected_date_str = ref_d.isoformat()

        # Feasibility determination
        is_feasible = True
        feasibility_reason = "Feasible within monthly financial capacity."
        if not is_completed:
            total_req_monthly += req_monthly
            if req_monthly > capacity:
                is_feasible = False
                feasibility_reason = f"Required monthly contribution (${req_monthly}) exceeds total available monthly capacity (${capacity})."
            elif req_contrib_res and not req_contrib_res.is_feasible:
                is_feasible = False
                feasibility_reason = req_contrib_res.warning_or_error or "Target date is impossible or requires excessive funding."

        evaluations.append({
            "id": g.get("id"),
            "name": g.get("name"),
            "category": g.get("category", "General"),
            "priority": g.get("priority", "medium"),
            "status": status,
            "target_amount": str(target),
            "current_amount": str(curr),
            "remaining_amount": str(rem),
            "progress_percentage": str(progress_pct),
            "target_date": str(target_dt) if target_dt else None,
            "monthly_contribution": str(quantize_currency(to_decimal(user_contrib))) if user_contrib is not None else None,
            "required_monthly_contribution": str(req_monthly),
            "months_remaining_deadline": months_left,
            "months_to_projected_completion": timeline_res.months_to_complete,
            "projected_completion_date": projected_date_str,
            "is_feasible": is_feasible,
            "is_completed": is_completed,
            "feasibility_explanation": feasibility_reason,
            "shortfall_or_surplus": str(quantize_currency(capacity - req_monthly)),
        })

    total_rem = quantize_currency(max(DECIMAL_ZERO, total_target - total_saved))
    overall_progress = quantize_percentage((total_saved / total_target * DECIMAL_ONE_HUNDRED) if total_target > DECIMAL_ZERO else DECIMAL_ONE_HUNDRED)
    net_surplus_or_shortfall = quantize_currency(capacity - total_req_monthly)
    conflict_detected = (total_req_monthly > capacity) and (active_count > 0)
    is_portfolio_feasible = not conflict_detected

    # Generate conflict alternatives if conflict exists
    conflict_alternatives: List[GoalConflictStrategy] = []
    if conflict_detected:
        goals_for_conflict = [
            {
                "id": ev["id"],
                "name": ev["name"],
                "priority": ev["priority"],
                "target_amount": ev["target_amount"],
                "current_amount": ev["current_amount"],
                "required_monthly": ev["required_monthly_contribution"],
                "status": ev["status"],
            }
            for ev in evaluations
            if not ev["is_completed"]
        ]
        conflict_alternatives = generate_goal_conflict_strategies(goals_for_conflict, capacity)

    if conflict_detected:
        summary_msg = (
            f"Goal Conflict Detected: Total active goals require ${total_req_monthly}/month, "
            f"exceeding available monthly capacity (${capacity}) by ${abs(net_surplus_or_shortfall)}. "
            f"Review structured rebalancing alternatives."
        )
    elif active_count > 0:
        summary_msg = (
            f"All active goals are feasible. Total monthly requirement is ${total_req_monthly}, "
            f"leaving a monthly surplus buffer of ${net_surplus_or_shortfall}."
        )
    else:
        summary_msg = "No active goals requiring monthly contributions."

    return GoalPortfolioAnalysisResult(
        total_target_amount=total_target,
        total_saved_amount=total_saved,
        total_remaining_amount=total_rem,
        overall_progress_percentage=overall_progress,
        total_required_monthly=total_req_monthly,
        available_monthly_capacity=capacity,
        net_monthly_surplus_or_shortfall=net_surplus_or_shortfall,
        is_portfolio_feasible=is_portfolio_feasible,
        conflict_detected=conflict_detected,
        active_goals_count=active_count,
        achieved_goals_count=achieved_count,
        goal_evaluations=evaluations,
        conflict_alternatives=conflict_alternatives,
        summary_explanation=summary_msg,
    )

