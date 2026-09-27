import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.decision_history import DecisionHistory
from app.models.user import User
from app.schemas.decision_memory import (
    DecisionMemoryCreateSchema,
    DecisionMemoryItemSchema,
    ProactiveInsightSchema,
)
from app.services.decision_memory_service import (
    evaluate_memory_drift,
    generate_proactive_insights,
    retrieve_relevant_memory,
    save_decision_memory,
)

logger = logging.getLogger("finpilot.api.decisions")

router = APIRouter(prefix="/decisions", tags=["Decision Memory & Proactive Insights"])


@router.get("/memory", response_model=List[DecisionMemoryItemSchema])
def list_decision_memories(
    q: Optional[str] = Query(None, description="Search keyword across decisions, actions, and items"),
    decision_type: Optional[str] = Query(None, description="Filter by decision type"),
    item_name: Optional[str] = Query(None, description="Filter by item name"),
    goal_name: Optional[str] = Query(None, description="Filter by goal"),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves previous financial decision memories for the authenticated user.
    """
    records = retrieve_relevant_memory(
        db=db,
        user_id=current_user.id,
        query=q,
        decision_type=decision_type,
        item_name=item_name,
        goal_name=goal_name,
        limit=limit,
    )
    
    # Attach live drift assessment for each record
    results = []
    for rec in records:
        item = DecisionMemoryItemSchema.model_validate(rec)
        try:
            item.drift_assessment = evaluate_memory_drift(db, current_user.id, rec)
        except Exception as e:
            logger.warning(f"Could not compute drift for decision {rec.id}: {e}")
        results.append(item)
        
    return results


@router.get("/memory/{decision_id}", response_model=DecisionMemoryItemSchema)
def get_decision_memory_detail(
    decision_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves full details of a specific decision memory, including drift assessment.
    Ensures user isolation.
    """
    record = db.query(DecisionHistory).filter(
        DecisionHistory.id == decision_id,
        DecisionHistory.user_id == current_user.id,
    ).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision memory record not found",
        )
        
    item = DecisionMemoryItemSchema.model_validate(record)
    item.drift_assessment = evaluate_memory_drift(db, current_user.id, record)
    return item


@router.post("/memory", response_model=DecisionMemoryItemSchema, status_code=status.HTTP_201_CREATED)
def create_decision_memory(
    data: DecisionMemoryCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Stores a structured decision memory for the authenticated user.
    """
    record = save_decision_memory(db, current_user.id, data)
    item = DecisionMemoryItemSchema.model_validate(record)
    item.drift_assessment = evaluate_memory_drift(db, current_user.id, record)
    return item


@router.get("/insights", response_model=List[ProactiveInsightSchema])
def get_proactive_insights_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates grounded, proactive financial opportunities and insights from live data and past decisions.
    """
    return generate_proactive_insights(db, current_user.id)
