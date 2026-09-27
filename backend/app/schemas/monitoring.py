from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FinancialChangeSchema(BaseModel):
    metric: str
    baseline: str
    current: str
    absolute_change: str
    percentage_change: str
    severity: str  # "low", "medium", "high", "critical"
    source: str = "financial_engine"
    description: str


class MonitoringSnapshotSchema(BaseModel):
    monthly_income: str
    monthly_essential_expenses: str
    monthly_discretionary_expenses: str
    monthly_total_expenses: str
    current_savings: str
    monthly_debt_payment: str
    savings_rate: str
    safe_to_spend_daily: str
    emergency_runway_months: str
    emergency_runway_status: str
    financial_health_score: str
    financial_health_grade: str
    budget_variance: str
    recurring_commitments_monthly: str
    active_goals_count: int
    goals_monthly_required: str
    goals_monthly_capacity: str
    goals_feasible: bool
    timestamp: datetime


class ReplanningAssessmentSchema(BaseModel):
    replanning_required: bool
    trigger: str
    severity: str
    affected_areas: List[str] = []
    reasons: List[str] = []
    recommendations: List[str] = []


class PlanComparisonItemSchema(BaseModel):
    area: str
    metric: str
    baseline_value: str
    proposed_value: str
    delta: str
    explanation: str


class GoalImpactSummarySchema(BaseModel):
    goal_name: str
    previous_contribution: str
    proposed_contribution: str
    timeline_delay_months: int
    status: str  # "on_track", "delayed"


class PlanComparisonTableSchema(BaseModel):
    items: List[PlanComparisonItemSchema]
    summary: str
    affected_goals: List[GoalImpactSummarySchema] = []


class ReplanningStrategyOptionSchema(BaseModel):
    strategy_id: str
    title: str
    description: str
    adjusted_essential: str
    adjusted_savings: str
    adjusted_discretionary: str
    resulting_buffer: str
    impact_on_goals: str
    tradeoffs: List[str] = []


class MonitoringRunResponse(BaseModel):
    baseline_snapshot: MonitoringSnapshotSchema
    current_snapshot: MonitoringSnapshotSchema
    changes: List[FinancialChangeSchema]
    assessment: ReplanningAssessmentSchema
    plan_comparison: Optional[PlanComparisonTableSchema] = None
    strategies: List[ReplanningStrategyOptionSchema] = []
    ai_explanation: Optional[str] = None
    plan_status: str = "on_track"  # "on_track", "needs_attention", "replanning_required"


class MonitoringStatusResponse(BaseModel):
    has_baseline: bool
    last_monitored_at: Optional[datetime] = None
    plan_status: str  # "on_track", "needs_attention", "replanning_required"
    replanning_required: bool
    critical_changes_count: int
    high_changes_count: int
    summary_message: str
