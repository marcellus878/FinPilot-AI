import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.security import get_current_user
from app.core.database import get_db
from app.models.hitl import RecommendationReview
from app.models.user import User

router = APIRouter()


class HITLReviewCreate(BaseModel):
    action: str  # "accepted", "modified", "rejected"
    agent_name: str = "Advisor"
    decision_id: Optional[str] = None
    user_notes: Optional[str] = None
    original_recommendation: Optional[Dict[str, Any]] = None
    modified_recommendation: Optional[Dict[str, Any]] = None


@router.post("/recommendations/{recommendation_id}/review")
def review_recommendation(
    recommendation_id: str,
    payload: HITLReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Human-in-the-Loop review endpoint:
    Allows user to explicitly Accept, Modify, or Reject an AI financial recommendation.
    """
    if payload.action not in ("accepted", "modified", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'accepted', 'modified', or 'rejected'",
        )

    review = RecommendationReview(
        id=uuid.uuid4(),
        user_id=current_user.id,
        recommendation_id=recommendation_id,
        decision_id=payload.decision_id,
        agent_name=payload.agent_name,
        action=payload.action,
        user_notes=payload.user_notes,
        original_recommendation=payload.original_recommendation,
        modified_recommendation=payload.modified_recommendation,
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return {
        "status": "success",
        "review_id": str(review.id),
        "action": review.action,
        "recommendation_id": recommendation_id,
        "message": f"Recommendation successfully {review.action} by human user.",
    }


@router.get("/reviews")
def get_user_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve history of human review decisions."""
    reviews = (
        db.query(RecommendationReview)
        .filter(RecommendationReview.user_id == current_user.id)
        .order_by(RecommendationReview.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "recommendation_id": r.recommendation_id,
            "agent_name": r.agent_name,
            "action": r.action,
            "user_notes": r.user_notes,
            "original_recommendation": r.original_recommendation,
            "modified_recommendation": r.modified_recommendation,
            "created_at": r.created_at.isoformat(),
        }
        for r in reviews
    ]
