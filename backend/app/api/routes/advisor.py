from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.graph import run_advisor_agent
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.advisor import (
    AdvisorChatRequest,
    AdvisorChatResponse,
    AdvisorRecommendationItem,
    AgentTraceItem,
    FinancialFactItem,
    RAGCitationResponseItem,
    ReflectionAuditItem,
)

router = APIRouter()


@router.post("/chat", response_model=AdvisorChatResponse, status_code=status.HTTP_200_OK)
def chat_with_advisor(
    request: AdvisorChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdvisorChatResponse:
    """
    Executes the FinPilot AI LangGraph Agentic Advisor pipeline.
    Reasons strictly over deterministic financial calculations for the authenticated user,
    augmented with Agentic RAG and deterministic Reflection & Self-Correction.
    """
    try:
        final_state = run_advisor_agent(
            db=db,
            user_id=current_user.id,
            query=request.message,
        )

        # Optionally persist new recommendations into database
        recs_from_state = final_state.get("recommendations", [])
        for r in recs_from_state:
            try:
                rec_record = Recommendation(
                    id=uuid.UUID(r["id"]) if r.get("id") else uuid.uuid4(),
                    user_id=current_user.id,
                    recommendation_type=r.get("type", "general"),
                    message=f"{r.get('title')}: {r.get('description')}",
                    status="active",
                )
                db.add(rec_record)
                db.commit()
            except Exception:
                db.rollback()

        health_ctx = final_state.get("financial_context", {}).get("financial_health_score", {})
        overall_health_score = health_ctx.get("overall_score")

        refl = final_state.get("reflection_audit")
        reflection_obj = ReflectionAuditItem(**refl) if refl else None

        return AdvisorChatResponse(
            request_id=final_state.get("request_id", str(uuid.uuid4())),
            user_id=str(current_user.id),
            query=final_state.get("query", request.message),
            intent=final_state.get("intent", "general_financial_question"),
            response=final_state.get("agent_response", "Advisory response generated."),
            financial_facts=[FinancialFactItem(**f) for f in final_state.get("financial_facts", [])],
            rag_citations=[RAGCitationResponseItem(**c) for c in final_state.get("rag_citations", [])],
            recommendations=[AdvisorRecommendationItem(**r) for r in final_state.get("recommendations", [])],
            reflection_audit=reflection_obj,
            execution_trace=[AgentTraceItem(**t) for t in final_state.get("execution_trace", [])],
            financial_health_score=overall_health_score,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Agent execution failed: {str(e)}")


@router.get("/recommendations", response_model=List[AdvisorRecommendationItem], status_code=status.HTTP_200_OK)
def get_user_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AdvisorRecommendationItem]:
    """Retrieves all active recommendations for the authenticated user."""
    recs = db.scalars(
        select(Recommendation)
        .where(Recommendation.user_id == current_user.id)
        .order_by(Recommendation.created_at.desc())
        .limit(20)
    ).all()

    return [
        AdvisorRecommendationItem(
            id=str(r.id),
            type=r.recommendation_type,
            title=r.recommendation_type.replace("_", " ").title(),
            description=r.message,
            priority="medium",
            category=None,
            hitl_status="pending_review",
        )
        for r in recs
    ]
