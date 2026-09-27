from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.salary import (
    MonthlyFinancialPlanResponse,
    RecurringCommitmentCreate,
    RecurringCommitmentResponse,
    RecurringCommitmentUpdate,
    SafeToSpendResponse,
    SalaryAllocationCalculateRequest,
    SalaryAllocationResponse,
    SalaryProfileResponse,
    SalaryProfileUpdate,
    SurvivalProjectionResponse,
)
from app.services.salary_service import (
    calculate_custom_allocation,
    create_recurring_commitment,
    delete_recurring_commitment,
    get_or_recalculate_monthly_plan,
    get_safe_to_spend,
    get_salary_allocation,
    get_salary_profile,
    get_survival_projection,
    list_recurring_commitments,
    update_recurring_commitment,
    update_salary_profile,
)

router = APIRouter()


# ---------------- Salary Profile Endpoints ----------------

@router.get("/profile", response_model=SalaryProfileResponse, status_code=status.HTTP_200_OK)
def get_user_salary_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SalaryProfileResponse:
    return get_salary_profile(db, current_user.id)


@router.post("/profile", response_model=SalaryProfileResponse, status_code=status.HTTP_200_OK)
@router.put("/profile", response_model=SalaryProfileResponse, status_code=status.HTTP_200_OK)
def save_user_salary_profile(
    profile_in: SalaryProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SalaryProfileResponse:
    return update_salary_profile(db, current_user.id, profile_in)


# ---------------- Recurring Expenses Endpoints ----------------

@router.get("/recurring-expenses", response_model=List[RecurringCommitmentResponse], status_code=status.HTTP_200_OK)
def get_user_recurring_commitments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[RecurringCommitmentResponse]:
    return list_recurring_commitments(db, current_user.id)


@router.post("/recurring-expenses", response_model=RecurringCommitmentResponse, status_code=status.HTTP_201_CREATED)
def add_recurring_commitment(
    item_in: RecurringCommitmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringCommitmentResponse:
    return create_recurring_commitment(db, current_user.id, item_in)


@router.put("/recurring-expenses/{commitment_id}", response_model=RecurringCommitmentResponse, status_code=status.HTTP_200_OK)
def edit_recurring_commitment(
    commitment_id: str,
    item_in: RecurringCommitmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecurringCommitmentResponse:
    res = update_recurring_commitment(db, current_user.id, commitment_id, item_in)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring commitment not found")
    return res


@router.delete("/recurring-expenses/{commitment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_recurring_commitment(
    commitment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = delete_recurring_commitment(db, current_user.id, commitment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recurring commitment not found")
    return None


# ---------------- Allocation & Calculation Endpoints ----------------

@router.get("/allocation", response_model=SalaryAllocationResponse, status_code=status.HTTP_200_OK)
def get_current_salary_allocation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SalaryAllocationResponse:
    return get_salary_allocation(db, current_user.id)


@router.post("/allocation/calculate", response_model=SalaryAllocationResponse, status_code=status.HTTP_200_OK)
def calculate_salary_allocation_preview(
    req: SalaryAllocationCalculateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SalaryAllocationResponse:
    return calculate_custom_allocation(db, current_user.id, req)


# ---------------- Safe to Spend & Survival Projection ----------------

@router.get("/safe-to-spend", response_model=SafeToSpendResponse, status_code=status.HTTP_200_OK)
def get_user_safe_to_spend(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SafeToSpendResponse:
    return get_safe_to_spend(db, current_user.id)


@router.get("/survival-projection", response_model=SurvivalProjectionResponse, status_code=status.HTTP_200_OK)
def get_user_survival_projection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SurvivalProjectionResponse:
    return get_survival_projection(db, current_user.id)


# ---------------- Monthly Financial Plan ----------------

@router.get("/monthly-plan", response_model=MonthlyFinancialPlanResponse, status_code=status.HTTP_200_OK)
@router.post("/monthly-plan/recalculate", response_model=MonthlyFinancialPlanResponse, status_code=status.HTTP_200_OK)
def get_monthly_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MonthlyFinancialPlanResponse:
    return get_or_recalculate_monthly_plan(db, current_user.id)
