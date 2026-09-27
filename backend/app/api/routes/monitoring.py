from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.monitoring import (
    FinancialChangeSchema,
    MonitoringRunResponse,
    MonitoringStatusResponse,
    PlanComparisonTableSchema,
)
from app.services.monitoring_service import (
    get_detected_changes,
    get_monitoring_status,
    get_replanning_proposal,
    run_monitoring_cycle,
)

router = APIRouter()


@router.get("/status", response_model=MonitoringStatusResponse, status_code=status.HTTP_200_OK)
def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MonitoringStatusResponse:
    return get_monitoring_status(db, current_user.id)


@router.post("/run", response_model=MonitoringRunResponse, status_code=status.HTTP_200_OK)
def run_monitoring(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MonitoringRunResponse:
    return run_monitoring_cycle(db, current_user.id)


@router.get("/changes", response_model=List[FinancialChangeSchema], status_code=status.HTTP_200_OK)
def get_changes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[FinancialChangeSchema]:
    return get_detected_changes(db, current_user.id)


@router.get("/replanning", response_model=Optional[PlanComparisonTableSchema], status_code=status.HTTP_200_OK)
def get_replanning(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Optional[PlanComparisonTableSchema]:
    return get_replanning_proposal(db, current_user.id)
