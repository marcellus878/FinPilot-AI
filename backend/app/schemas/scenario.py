from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScenarioSimulateRequest(BaseModel):
    scenario_type: str = Field(
        ...,
        description="Type of scenario: one_time_purchase, new_recurring_expense, income_change, unexpected_expense",
    )
    amount: Decimal = Field(..., description="Amount of expense or income adjustment")
    name: Optional[str] = Field(default="Proposed Decision", max_length=200)
    timing_months: int = Field(
        default=0,
        ge=0,
        le=60,
        description="Timing offset in months (0 = this month / immediate, 1..60 for delayed decisions)",
    )
    description: Optional[str] = Field(default=None, max_length=500)


class FinancialMetricsSnapshotSchema(BaseModel):
    monthly_income: str
    monthly_essential_expenses: str
    monthly_debt_payments: str
    monthly_disposable_income: str
    current_savings: str
    savings_rate: str
    debt_to_income_ratio: str
    emergency_fund_months: str
    emergency_fund_status: str
    daily_safe_to_spend: str
    financial_health_score: str
    financial_health_grade: str


class FinancialMetricsDeltaSchema(BaseModel):
    monthly_income_delta: str
    monthly_essential_expenses_delta: str
    monthly_disposable_income_delta: str
    savings_delta: str
    savings_rate_delta: str
    debt_to_income_delta: str
    emergency_fund_months_delta: str
    daily_safe_to_spend_delta: str
    financial_health_score_delta: str


class GoalScenarioImpactSchema(BaseModel):
    goal_id: str
    goal_name: str
    target_amount: str
    current_amount: str
    previous_monthly_contribution: str
    new_monthly_contribution: str
    previous_months_to_complete: int
    new_months_to_complete: int
    timeline_delay_months: Optional[int] = None
    is_still_feasible: bool
    explanation: str


from app.schemas.decision import DecisionResult


class ScenarioSimulateResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    scenario_type: str
    amount: str
    timing_months: int
    description: Optional[str] = None
    is_sustainable: bool
    affordability_verdict: str  # "safe", "stretched", "unaffordable"
    before_state: FinancialMetricsSnapshotSchema
    after_state: FinancialMetricsSnapshotSchema
    delta: FinancialMetricsDeltaSchema
    goal_impacts: List[GoalScenarioImpactSchema]
    warnings: List[str]
    tradeoffs: List[str]
    recommendation: str
    ai_explanation: Optional[str] = None
    decision_result: Optional[DecisionResult] = None


class ScenarioCompareItemRequest(BaseModel):
    id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field(..., description="one_time_purchase, new_recurring_expense, income_change, unexpected_expense")
    amount: Decimal = Field(..., description="Amount for this scenario")
    timing_months: int = Field(default=0, ge=0, le=60)
    description: Optional[str] = None


class ScenarioCompareRequest(BaseModel):
    scenarios: List[ScenarioCompareItemRequest] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="List of 1 to 3 scenarios to compare side-by-side against baseline",
    )


class ScenarioTradeoffSummaryItem(BaseModel):
    scenario_id: str
    scenario_name: str
    verdict: str
    ending_savings: str
    monthly_cash_flow: str
    emergency_runway_months: str
    health_score: str
    health_score_change: str
    key_tradeoffs: List[str]
    recommendation: str


class ScenarioCompareResponse(BaseModel):
    baseline: FinancialMetricsSnapshotSchema
    scenarios: List[ScenarioSimulateResponse]
    tradeoff_summary: List[ScenarioTradeoffSummaryItem]
