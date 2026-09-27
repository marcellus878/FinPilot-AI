from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate,
    BudgetPerformanceResponse,
    BudgetResponse,
    BudgetUpdate,
)
from app.services.budget_service import (
    create_or_update_budget,
    delete_budget,
    get_budget,
    get_user_budget_performance,
    list_budgets,
    update_budget,
)

router = APIRouter()


@router.get("", response_model=List[BudgetResponse], status_code=status.HTTP_200_OK)
def get_budgets(
    period: Optional[str] = Query(None, description="Filter by budget period (e.g. monthly)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[BudgetResponse]:
    return list_budgets(db=db, user_id=current_user.id, period=period)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_or_upsert_budget(
    budget_in: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetResponse:
    return create_or_update_budget(db=db, user_id=current_user.id, budget_in=budget_in)


@router.get("/performance", response_model=BudgetPerformanceResponse, status_code=status.HTTP_200_OK)
@router.get("/summary", response_model=BudgetPerformanceResponse, status_code=status.HTTP_200_OK)
def get_budget_performance(
    period: str = Query("monthly", description="Budget period"),
    start_date: Optional[datetime] = Query(None, description="Start date of analysis period"),
    end_date: Optional[datetime] = Query(None, description="End date of analysis period"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetPerformanceResponse:
    return get_user_budget_performance(
        db=db,
        user_id=current_user.id,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/{budget_id}", response_model=BudgetResponse, status_code=status.HTTP_200_OK)
def get_budget_by_id(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetResponse:
    budget = get_budget(db=db, user_id=current_user.id, budget_id=budget_id)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget


@router.put("/{budget_id}", response_model=BudgetResponse, status_code=status.HTTP_200_OK)
def update_existing_budget(
    budget_id: UUID,
    budget_in: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetResponse:
    budget = update_budget(db=db, user_id=current_user.id, budget_id=budget_id, budget_in=budget_in)
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = delete_budget(db=db, user_id=current_user.id, budget_id=budget_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return None
