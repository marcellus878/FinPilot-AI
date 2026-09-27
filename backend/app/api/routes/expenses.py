from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.transaction import (
    CategorySpendingResponse,
    ExpenseSummaryResponse,
)
from app.services.transaction_service import (
    get_user_category_spending,
    get_user_expense_summary,
)

router = APIRouter()


@router.get("/summary", response_model=ExpenseSummaryResponse, status_code=status.HTTP_200_OK)
def get_expense_summary(
    start_date: Optional[datetime] = Query(None, description="Start date of summary window"),
    end_date: Optional[datetime] = Query(None, description="End date of summary window"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ExpenseSummaryResponse:
    return get_user_expense_summary(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/categories", response_model=List[CategorySpendingResponse], status_code=status.HTTP_200_OK)
def get_category_spending(
    start_date: Optional[datetime] = Query(None, description="Start date of window"),
    end_date: Optional[datetime] = Query(None, description="End date of window"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[CategorySpendingResponse]:
    return get_user_category_spending(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )
