from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class AlternativeStrategySchema(BaseModel):
    id: str
    title: str
    description: str
    timeline_delay_months: int = 0
    tradeoffs: List[str] = []


class DecisionMemoryCreateSchema(BaseModel):
    user_action: str
    decision: str
    decision_type: str = "general_decision"
    item_name: Optional[str] = None
    amount: Optional[str] = None
    strategy_selected: Optional[str] = None
    alternatives_considered: Optional[List[Dict[str, Any]]] = None
    affected_goals: Optional[List[str]] = None
    baseline_metrics: Optional[Dict[str, Any]] = None
    resulting_metrics: Optional[Dict[str, Any]] = None
    assumptions: Optional[List[str]] = None
    recommendation_summary: Optional[str] = None
    financial_impact: Optional[Dict[str, Any]] = None
    status: str = "active"


class DecisionMemoryDriftSchema(BaseModel):
    decision_id: str
    decision_type: str
    item_name: Optional[str] = None
    created_at: datetime
    has_drifted: bool
    drift_severity: str  # "none", "low", "medium", "high"
    metrics_comparison: Dict[str, Dict[str, Any]]  # metric: {baseline, current, delta, changed}
    explanation: str
    can_re_evaluate: bool


class DecisionMemoryItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    user_action: str
    decision: str
    decision_type: str
    item_name: Optional[str] = None
    amount: Optional[str] = None
    strategy_selected: Optional[str] = None
    alternatives_considered: Optional[List[Any]] = None
    affected_goals: Optional[List[str]] = None
    baseline_metrics: Optional[Dict[str, Any]] = None
    resulting_metrics: Optional[Dict[str, Any]] = None
    assumptions: Optional[List[str]] = None
    recommendation_summary: Optional[str] = None
    financial_impact: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    drift_assessment: Optional[DecisionMemoryDriftSchema] = None



class ProactiveInsightSchema(BaseModel):
    id: str
    insight_type: str  # "drift_opportunity", "goal_risk", "spending_anomaly", "rebalancing_opportunity", "decision_revisit"
    title: str
    description: str
    severity: str  # "info", "low", "medium", "high", "critical"
    related_decision_id: Optional[str] = None
    related_goal: Optional[str] = None
    metric_facts: List[Dict[str, Any]] = []
    action_prompt: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
