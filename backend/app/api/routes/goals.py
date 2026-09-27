from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.goal import (
    GoalAnalysisResponse,
    GoalConflictResponse,
    GoalCreate,
    GoalResponse,
    GoalUpdate,
)
from app.services.goal_service import (
    analyze_user_goals,
    create_goal,
    delete_goal,
    get_goal_by_id,
    get_goals,
    get_user_goal_conflicts,
    update_goal,
)

router = APIRouter()


@router.get("", response_model=List[GoalResponse], status_code=status.HTTP_200_OK)
def list_goals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[GoalResponse]:
    return get_goals(db, current_user.id)


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_new_goal(
    goal_in: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalResponse:
    return create_goal(db, current_user.id, goal_in)


@router.get("/analysis", response_model=GoalAnalysisResponse, status_code=status.HTTP_200_OK)
def get_goals_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalAnalysisResponse:
    return analyze_user_goals(db, current_user.id)


@router.get("/conflicts", response_model=GoalConflictResponse, status_code=status.HTTP_200_OK)
def get_goals_conflicts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalConflictResponse:
    return get_user_goal_conflicts(db, current_user.id)


@router.get("/{goal_id}", response_model=GoalResponse, status_code=status.HTTP_200_OK)
def get_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalResponse:
    goal = get_goal_by_id(db, current_user.id, goal_id)
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return goal


@router.put("/{goal_id}", response_model=GoalResponse, status_code=status.HTTP_200_OK)
def update_existing_goal(
    goal_id: UUID,
    goal_in: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GoalResponse:
    updated = update_goal(db, current_user.id, goal_id, goal_in)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return updated


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_goal(
    goal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = delete_goal(db, current_user.id, goal_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return None
