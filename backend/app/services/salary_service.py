from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from uuid import UUID

from sqlalchemy.orm import Session

from app.financial_engine import (
    AllocationAlternative,
    SafeToSpendResult,
    SalaryAllocationResult,
    SalaryCycleDates,
    SurvivalProjectionResult,
    calculate_monthly_recurring_commitments,
    calculate_safe_to_spend,
    calculate_salary_allocation,
    calculate_salary_cycle_dates,
    calculate_survival_projection,
    quantize_currency,
    to_decimal,
)
from app.models.financial_plan import FinancialPlan
from app.models.financial_profile import FinancialProfile
from app.models.transaction import Transaction
from app.schemas.salary import (
    AllocationAlternativeResponse,
    MonthlyFinancialPlanResponse,
    RecurringCommitmentCreate,
    RecurringCommitmentResponse,
    RecurringCommitmentUpdate,
    SafeToSpendResponse,
    SalaryAllocationCalculateRequest,
    SalaryAllocationResponse,
    SalaryProfileCreate,
    SalaryProfileResponse,
    SalaryProfileUpdate,
    SurvivalProjectionResponse,
)


def get_or_create_financial_plan(
    db: Session,
    user_id: UUID,
) -> FinancialPlan:
    """
    Retrieves the active FinancialPlan record for a user or creates a default one.
    """
    plan = (
        db.query(FinancialPlan)
        .filter(FinancialPlan.user_id == user_id, FinancialPlan.is_active.is_(True))
        .first()
    )

    if not plan:
        # Check financial profile for income defaults
        profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
        base_income = float(profile.monthly_income) if profile else 0.0

        default_data = {
            "salary_profile": {
                "monthly_income": str(base_income),
                "expected_salary_day": 1,
                "additional_recurring_income": "0.00",
                "savings_target": None,
                "essential_spending_allowance": None,
                "discretionary_allowance": None,
            },
            "recurring_commitments": [],
        }

        plan = FinancialPlan(
            user_id=user_id,
            plan_data=default_data,
            is_active=True,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

    return plan


def get_salary_profile(
    db: Session,
    user_id: UUID,
) -> SalaryProfileResponse:
    plan = get_or_create_financial_plan(db, user_id)
    p_data = plan.plan_data.get("salary_profile", {})

    profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
    raw_income = p_data.get("monthly_income")
    if raw_income is None or Decimal(str(raw_income)) == Decimal("0.00"):
        if profile and profile.monthly_income > Decimal("0.00"):
            monthly_income = profile.monthly_income
        else:
            monthly_income = Decimal("0.00")
    else:
        monthly_income = to_decimal(raw_income)

    expected_day = int(p_data.get("expected_salary_day", 1))
    additional_income = to_decimal(p_data.get("additional_recurring_income", "0.00"))
    savings_target = to_decimal(p_data["savings_target"]) if p_data.get("savings_target") is not None else None
    essential_allowance = to_decimal(p_data["essential_spending_allowance"]) if p_data.get("essential_spending_allowance") is not None else None
    disc_allowance = to_decimal(p_data["discretionary_allowance"]) if p_data.get("discretionary_allowance") is not None else None

    total_monthly = monthly_income + additional_income
    cycle_dates = calculate_salary_cycle_dates(expected_salary_day=expected_day)

    return SalaryProfileResponse(
        monthly_income=monthly_income,
        expected_salary_day=expected_day,
        additional_recurring_income=additional_income,
        savings_target=savings_target,
        essential_spending_allowance=essential_allowance,
        discretionary_allowance=disc_allowance,
        total_monthly_income=total_monthly,
        cycle_start_date=cycle_dates.cycle_start_date,
        next_salary_date=cycle_dates.next_salary_date,
        days_in_cycle=cycle_dates.days_in_cycle,
        days_elapsed=cycle_dates.days_elapsed,
        days_remaining=cycle_dates.days_remaining,
    )


def update_salary_profile(
    db: Session,
    user_id: UUID,
    profile_in: SalaryProfileUpdate,
) -> SalaryProfileResponse:
    plan = get_or_create_financial_plan(db, user_id)
    data = dict(plan.plan_data)
    s_prof = dict(data.get("salary_profile", {}))

    update_dict = profile_in.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        if v is not None:
            s_prof[k] = str(v)

    data["salary_profile"] = s_prof
    plan.plan_data = data
    db.commit()
    db.refresh(plan)

    return get_salary_profile(db, user_id)


def list_recurring_commitments(
    db: Session,
    user_id: UUID,
) -> List[RecurringCommitmentResponse]:
    plan = get_or_create_financial_plan(db, user_id)
    raw_comms = plan.plan_data.get("recurring_commitments", [])
    salary_prof = get_salary_profile(db, user_id)

    items, _, _ = calculate_monthly_recurring_commitments(
        commitments=raw_comms,
        next_salary_date=salary_prof.next_salary_date,
    )

    return [
        RecurringCommitmentResponse(
            id=item.id,
            name=item.name,
            category=item.category,
            amount=item.amount,
            frequency=item.frequency,  # type: ignore
            monthly_equivalent=item.monthly_equivalent,
            next_expected_date=item.next_expected_date,
            description=None,
            is_active=item.is_active,
            is_confirmed=item.is_confirmed,
            is_due_in_current_cycle=item.is_due_in_current_cycle,
        )
        for item in items
    ]


def create_recurring_commitment(
    db: Session,
    user_id: UUID,
    item_in: RecurringCommitmentCreate,
) -> RecurringCommitmentResponse:
    plan = get_or_create_financial_plan(db, user_id)
    data = dict(plan.plan_data)
    comms = list(data.get("recurring_commitments", []))

    new_id = str(uuid.uuid4())
    new_item = {
        "id": new_id,
        "name": item_in.name.strip(),
        "category": item_in.category.strip(),
        "amount": str(item_in.amount),
        "frequency": item_in.frequency,
        "next_expected_date": item_in.next_expected_date.isoformat() if item_in.next_expected_date else None,
        "description": item_in.description.strip() if item_in.description else None,
        "is_active": item_in.is_active,
        "is_confirmed": item_in.is_confirmed,
    }
    comms.append(new_item)
    data["recurring_commitments"] = comms
    plan.plan_data = data
    db.commit()
    db.refresh(plan)

    all_items = list_recurring_commitments(db, user_id)
    created = next((i for i in all_items if i.id == new_id), None)
    if created:
        return created

    return RecurringCommitmentResponse(
        id=new_id,
        name=item_in.name,
        category=item_in.category,
        amount=item_in.amount,
        frequency=item_in.frequency,
        monthly_equivalent=item_in.amount,
        next_expected_date=item_in.next_expected_date,
        description=item_in.description,
        is_active=item_in.is_active,
        is_confirmed=item_in.is_confirmed,
        is_due_in_current_cycle=True,
    )


def update_recurring_commitment(
    db: Session,
    user_id: UUID,
    commitment_id: str,
    item_in: RecurringCommitmentUpdate,
) -> Optional[RecurringCommitmentResponse]:
    plan = get_or_create_financial_plan(db, user_id)
    data = dict(plan.plan_data)
    comms = list(data.get("recurring_commitments", []))

    target = None
    for idx, c in enumerate(comms):
        if str(c.get("id")) == commitment_id:
            updated = dict(c)
            up_data = item_in.model_dump(exclude_unset=True)
            for k, v in up_data.items():
                if v is not None:
                    if isinstance(v, datetime):
                        updated[k] = v.isoformat()
                    elif isinstance(v, Decimal):
                        updated[k] = str(v)
                    else:
                        updated[k] = v
            comms[idx] = updated
            target = updated
            break

    if not target:
        return None

    data["recurring_commitments"] = comms
    plan.plan_data = data
    db.commit()
    db.refresh(plan)

    all_items = list_recurring_commitments(db, user_id)
    return next((i for i in all_items if i.id == commitment_id), None)


def delete_recurring_commitment(
    db: Session,
    user_id: UUID,
    commitment_id: str,
) -> bool:
    plan = get_or_create_financial_plan(db, user_id)
    data = dict(plan.plan_data)
    comms = list(data.get("recurring_commitments", []))

    initial_len = len(comms)
    filtered = [c for c in comms if str(c.get("id")) != commitment_id]
    if len(filtered) == initial_len:
        return False

    data["recurring_commitments"] = filtered
    plan.plan_data = data
    db.commit()
    db.refresh(plan)
    return True


def get_salary_allocation(
    db: Session,
    user_id: UUID,
) -> SalaryAllocationResponse:
    profile = get_salary_profile(db, user_id)
    comms = list_recurring_commitments(db, user_id)
    total_fixed = sum((c.monthly_equivalent for c in comms if c.is_active), Decimal("0.00"))

    res = calculate_salary_allocation(
        monthly_income=profile.total_monthly_income,
        fixed_commitments=total_fixed,
        essential_allowance=profile.essential_spending_allowance,
        savings_target=profile.savings_target,
        discretionary_allowance=profile.discretionary_allowance,
    )

    alts = [
        AllocationAlternativeResponse(
            title=a.title,
            description=a.description,
            adjusted_savings_target=a.adjusted_savings_target,
            adjusted_essential_allowance=a.adjusted_essential_allowance,
            adjusted_discretionary_allowance=a.adjusted_discretionary_allowance,
            resulting_buffer=a.resulting_buffer,
        )
        for a in res.alternatives
    ]

    return SalaryAllocationResponse(
        monthly_income=res.monthly_income,
        fixed_commitments=res.fixed_commitments,
        essential_allowance=res.essential_allowance,
        savings_target=res.savings_target,
        discretionary_allowance=res.discretionary_allowance,
        remaining_buffer=res.remaining_buffer,
        fixed_percentage=res.fixed_percentage,
        essential_percentage=res.essential_percentage,
        savings_percentage=res.savings_percentage,
        discretionary_percentage=res.discretionary_percentage,
        buffer_percentage=res.buffer_percentage,
        is_feasible=res.is_feasible,
        deficit_amount=res.deficit_amount,
        explanation=res.explanation,
        alternatives=alts,
    )


def calculate_custom_allocation(
    db: Session,
    user_id: UUID,
    req: SalaryAllocationCalculateRequest,
) -> SalaryAllocationResponse:
    profile = get_salary_profile(db, user_id)
    income = req.monthly_income if req.monthly_income is not None else profile.total_monthly_income

    if req.fixed_commitments is not None:
        fixed = req.fixed_commitments
    else:
        comms = list_recurring_commitments(db, user_id)
        fixed = sum((c.monthly_equivalent for c in comms if c.is_active), Decimal("0.00"))

    res = calculate_salary_allocation(
        monthly_income=income,
        fixed_commitments=fixed,
        essential_allowance=req.essential_allowance,
        savings_target=req.savings_target,
        discretionary_allowance=req.discretionary_allowance,
    )

    alts = [
        AllocationAlternativeResponse(
            title=a.title,
            description=a.description,
            adjusted_savings_target=a.adjusted_savings_target,
            adjusted_essential_allowance=a.adjusted_essential_allowance,
            adjusted_discretionary_allowance=a.adjusted_discretionary_allowance,
            resulting_buffer=a.resulting_buffer,
        )
        for a in res.alternatives
    ]

    return SalaryAllocationResponse(
        monthly_income=res.monthly_income,
        fixed_commitments=res.fixed_commitments,
        essential_allowance=res.essential_allowance,
        savings_target=res.savings_target,
        discretionary_allowance=res.discretionary_allowance,
        remaining_buffer=res.remaining_buffer,
        fixed_percentage=res.fixed_percentage,
        essential_percentage=res.essential_percentage,
        savings_percentage=res.savings_percentage,
        discretionary_percentage=res.discretionary_percentage,
        buffer_percentage=res.buffer_percentage,
        is_feasible=res.is_feasible,
        deficit_amount=res.deficit_amount,
        explanation=res.explanation,
        alternatives=alts,
    )


def get_safe_to_spend(
    db: Session,
    user_id: UUID,
) -> SafeToSpendResponse:
    profile = get_salary_profile(db, user_id)
    fin_profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
    current_savings = fin_profile.current_savings if fin_profile else Decimal("0.00")

    # Current cycle dates
    cycle = calculate_salary_cycle_dates(expected_salary_day=profile.expected_salary_day)

    # Fetch transactions in current cycle
    txs = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= cycle.cycle_start_date,
            Transaction.transaction_date <= datetime.now(),
        )
        .all()
    )

    total_spent_cycle = sum((t.amount for t in txs if t.type == "expense"), Decimal("0.00"))
    total_income_cycle = sum((t.amount for t in txs if t.type == "income"), profile.total_monthly_income)

    # Current available balance
    current_available = total_income_cycle + current_savings - total_spent_cycle

    # Recurring commitments due in this cycle
    comms = list_recurring_commitments(db, user_id)
    upcoming_commitments = sum(
        (c.monthly_equivalent for c in comms if c.is_active and c.is_due_in_current_cycle),
        Decimal("0.00"),
    )

    # Remaining essential allowance
    essential_spent = sum(
        (t.amount for t in txs if t.type == "expense" and t.category in ["Groceries", "Rent/Housing", "Bills & Utilities", "Healthcare", "Education"]),
        Decimal("0.00"),
    )
    total_ess_allowance = profile.essential_spending_allowance or (profile.total_monthly_income * Decimal("0.25"))
    remaining_essential = max(Decimal("0.00"), total_ess_allowance - essential_spent)

    savings_reserve = profile.savings_target or (profile.total_monthly_income * Decimal("0.20"))

    res = calculate_safe_to_spend(
        current_available_funds=current_available,
        upcoming_commitments=upcoming_commitments,
        remaining_essential_allowance=remaining_essential,
        savings_reserve=savings_reserve,
        days_remaining=cycle.days_remaining,
    )

    return SafeToSpendResponse(
        current_available_funds=res.current_available_funds,
        upcoming_commitments=res.upcoming_commitments,
        remaining_essential_allowance=res.remaining_essential_allowance,
        savings_reserve=res.savings_reserve,
        emergency_reserve=res.emergency_reserve,
        total_committed_and_reserved=res.total_committed_and_reserved,
        safe_to_spend_amount=res.safe_to_spend_amount,
        daily_safe_to_spend=res.daily_safe_to_spend,
        days_remaining=res.days_remaining,
        explanation=res.explanation,
    )


def get_survival_projection(
    db: Session,
    user_id: UUID,
) -> SurvivalProjectionResult:
    profile = get_salary_profile(db, user_id)
    fin_profile = db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()
    current_savings = fin_profile.current_savings if fin_profile else Decimal("0.00")

    cycle = calculate_salary_cycle_dates(expected_salary_day=profile.expected_salary_day)

    # Cycle transactions
    txs = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= cycle.cycle_start_date,
            Transaction.transaction_date <= datetime.now(),
        )
        .all()
    )

    expense_txs = [t for t in txs if t.type == "expense"]
    total_spent_cycle = sum((t.amount for t in expense_txs), Decimal("0.00"))
    total_income_cycle = sum((t.amount for t in txs if t.type == "income"), profile.total_monthly_income)
    current_available = total_income_cycle + current_savings - total_spent_cycle

    days_elapsed = max(1, cycle.days_elapsed)
    daily_burn_rate = quantize_currency(total_spent_cycle / Decimal(str(days_elapsed)))

    comms = list_recurring_commitments(db, user_id)
    upcoming_commitments = sum(
        (c.monthly_equivalent for c in comms if c.is_active and c.is_due_in_current_cycle),
        Decimal("0.00"),
    )

    total_ess_allowance = profile.essential_spending_allowance or (profile.total_monthly_income * Decimal("0.25"))

    res = calculate_survival_projection(
        current_available_funds=current_available,
        monthly_income=profile.total_monthly_income,
        recent_average_daily_burn=daily_burn_rate,
        days_remaining=cycle.days_remaining,
        upcoming_commitments=upcoming_commitments,
        remaining_essential_allowance=total_ess_allowance,
    )

    return SurvivalProjectionResponse(
        current_available_funds=res.current_available_funds,
        recent_average_daily_burn=res.recent_average_daily_burn,
        days_remaining=res.days_remaining,
        upcoming_commitments=res.upcoming_commitments,
        projected_remaining_spend=res.projected_remaining_spend,
        projected_end_of_month_balance=res.projected_end_of_month_balance,
        daily_spending_capacity=res.daily_spending_capacity,
        status=res.status,  # type: ignore
        explanation=res.explanation,
        evidence=res.evidence,
    )


def get_or_recalculate_monthly_plan(
    db: Session,
    user_id: UUID,
) -> MonthlyFinancialPlanResponse:
    plan = get_or_create_financial_plan(db, user_id)

    prof = get_salary_profile(db, user_id)
    comms = list_recurring_commitments(db, user_id)
    alloc = get_salary_allocation(db, user_id)
    safe = get_safe_to_spend(db, user_id)
    surv = get_survival_projection(db, user_id)

    # Save calculated snapshot in plan_data
    data = dict(plan.plan_data)
    data["last_calculated_at"] = datetime.now().isoformat()
    plan.plan_data = data
    db.commit()
    db.refresh(plan)

    return MonthlyFinancialPlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        is_active=plan.is_active,
        salary_profile=prof,
        recurring_commitments=comms,
        allocation=alloc,
        safe_to_spend=safe,
        survival_projection=surv,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )
