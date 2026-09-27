import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GoalBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Name of the goal")
    target_amount: Decimal = Field(..., gt=0, description="Target total amount to save")
    current_amount: Decimal = Field(default=Decimal("0.00"), ge=0, description="Current amount already saved")
    target_date: Optional[date] = Field(default=None, description="Target date for goal completion")
    priority: str = Field(default="medium", description="Priority tier: low, medium, or high")
    category: str = Field(default="General", max_length=100, description="Category/Type of goal")
    monthly_contribution: Optional[Decimal] = Field(default=None, ge=0, description="Optional planned monthly contribution")
    status: str = Field(default="in_progress", description="Goal status: in_progress, achieved, paused, cancelled")


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    target_amount: Optional[Decimal] = Field(default=None, gt=0)
    current_amount: Optional[Decimal] = Field(default=None, ge=0)
    target_date: Optional[date] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    monthly_contribution: Optional[Decimal] = Field(default=None, ge=0)
    status: Optional[str] = None


class GoalResponse(GoalBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GoalAnalysisItem(BaseModel):
    id: str
    name: str
    category: str
    priority: str
    status: str
    target_amount: str
    current_amount: str
    remaining_amount: str
    progress_percentage: str
    target_date: Optional[str] = None
    monthly_contribution: Optional[str] = None
    required_monthly_contribution: str
    months_remaining_deadline: int
    months_to_projected_completion: int
    projected_completion_date: Optional[str] = None
    is_feasible: bool
    is_completed: bool
    feasibility_explanation: str
    shortfall_or_surplus: str


class GoalConflictAllocationItem(BaseModel):
    goal_id: str
    goal_name: str
    priority: str
    target_amount: str
    current_amount: str
    monthly_target_contribution: str
    allocated_amount: str
    is_fully_funded: bool
    shortfall: str


class GoalConflictStrategySchema(BaseModel):
    strategy_id: str
    strategy_name: str
    description: str
    allocations: List[GoalConflictAllocationItem]
    total_allocated: str
    remaining_unallocated: str
    fully_funded_count: int
    unfunded_count: int


class GoalAnalysisResponse(BaseModel):
    total_target_amount: str
    total_saved_amount: str
    total_remaining_amount: str
    overall_progress_percentage: str
    total_required_monthly: str
    available_monthly_capacity: str
    net_monthly_surplus_or_shortfall: str
    is_portfolio_feasible: bool
    conflict_detected: bool
    active_goals_count: int
    achieved_goals_count: int
    goal_evaluations: List[GoalAnalysisItem]
    conflict_alternatives: List[GoalConflictStrategySchema]
    summary_explanation: str


class GoalConflictResponse(BaseModel):
    conflict_detected: bool
    total_available_capacity: str
    total_required_monthly: str
    shortfall: str
    active_goals_count: int
    goals_involved: List[GoalAnalysisItem]
    strategies: List[GoalConflictStrategySchema]
    explanation: str
