from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

DecisionType = Literal[
    "one_time_purchase",
    "new_recurring_expense",
    "income_change",
    "unexpected_expense",
]


class DecisionRequest(BaseModel):
    decision_type: DecisionType = Field(
        default="one_time_purchase",
        description="Type of financial scenario / decision",
    )
    amount: Decimal = Field(
        ...,
        description="Monetary amount involved in the decision (positive for expense/increase, negative for income decrease)",
    )
    description: Optional[str] = Field(
        default=None,
        description="Name or description of the purchase/decision (e.g. Laptop, Rent)",
    )
    timing_months: int = Field(
        default=0,
        ge=0,
        description="Months to delay the decision/purchase",
    )
    recurring_monthly_cost: Optional[Decimal] = Field(
        default=None,
        description="Optional ongoing monthly cost (e.g. EMI or upkeep)",
    )
    duration_months: Optional[int] = Field(
        default=None,
        description="Optional duration in months for recurring/EMI decisions",
    )


class FinancialFactLabelValue(BaseModel):
    label: str
    value: Any
    unit: str = "currency"  # "currency", "percentage", "months", "score", "count"
    source: str = "financial_engine"


class DecisionImpactItem(BaseModel):
    area: str  # "safe_to_spend", "emergency_runway", "monthly_cash_flow", "goals", "health_score"
    description: str
    value: Any
    delta: Optional[str] = None


class DecisionOptionItem(BaseModel):
    title: str
    description: str
    impact: str


class DecisionScenarioMetadata(BaseModel):
    description: str
    assumptions: List[str] = []


class DecisionResult(BaseModel):
    summary: str
    scenario: DecisionScenarioMetadata
    financial_facts: List[FinancialFactLabelValue] = []
    impacts: List[DecisionImpactItem] = []
    tradeoffs: List[str] = []
    options: List[DecisionOptionItem] = []
    recommendation: str
    confidence: Literal["high", "medium", "low"] = "high"
    is_sustainable: bool = True
    affordability_verdict: str = "safe"
