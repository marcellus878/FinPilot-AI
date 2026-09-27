from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.scenario import (
    ScenarioCompareRequest,
    ScenarioCompareResponse,
    ScenarioSimulateRequest,
    ScenarioSimulateResponse,
)
from app.services.scenario_service import (
    compare_user_scenarios,
    simulate_user_scenario,
)

router = APIRouter()


@router.post("/simulate", response_model=ScenarioSimulateResponse, status_code=status.HTTP_200_OK)
def simulate_scenario(
    request: ScenarioSimulateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScenarioSimulateResponse:
    try:
        return simulate_user_scenario(db, current_user.id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/compare", response_model=ScenarioCompareResponse, status_code=status.HTTP_200_OK)
def compare_scenarios(
    request: ScenarioCompareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScenarioCompareResponse:
    try:
        return compare_user_scenarios(db, current_user.id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
