from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AdvisorChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="The user's question or financial query")
    context_override: Optional[Dict[str, Any]] = Field(default=None, description="Optional override values for what-if exploration")


class FinancialFactItem(BaseModel):
    metric: str
    value: Any
    category: Optional[str] = None
    interpretation: Optional[str] = None


class AdvisorRecommendationItem(BaseModel):
    id: Optional[str] = None
    type: str  # "expense_reduction", "budget_adjustment", "goal_acceleration", "habit_change", "general"
    title: str
    description: str
    potential_monthly_savings: Optional[float] = None
    priority: str = "medium"  # "high", "medium", "low"
    category: Optional[str] = None
    hitl_status: Optional[str] = "pending_review"  # "pending_review", "accepted", "modified", "rejected"


class AgentTraceItem(BaseModel):
    step: str
    agent: str
    action: str
    details: Dict[str, Any]
    timestamp: str


class RAGCitationResponseItem(BaseModel):
    source_id: str
    title: str
    publisher: str
    category: str
    url: Optional[str] = None
    relevant_excerpt: str


class ReflectionAuditItem(BaseModel):
    status: str
    groundedness_score: float
    issues_detected: List[str] = []
    corrections_applied: List[str] = []
    reflection_performed: bool = True
    rag_grounded: bool = False


class AdvisorChatResponse(BaseModel):
    request_id: str
    user_id: str
    query: str
    intent: str
    response: str
    financial_facts: List[FinancialFactItem] = []
    rag_citations: List[RAGCitationResponseItem] = []
    recommendations: List[AdvisorRecommendationItem] = []
    reflection_audit: Optional[ReflectionAuditItem] = None
    execution_trace: List[AgentTraceItem] = []
    financial_health_score: Optional[float] = None
