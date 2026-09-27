from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BudgetBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100, description="Budget category name")
    monthly_limit: Decimal = Field(..., ge=Decimal("0.00"), description="Monthly spending limit")
    period: str = Field(default="monthly", max_length=50, description="Budget period (e.g. monthly)")


class BudgetCreate(BudgetBase):
    pass


class BudgetUpdate(BaseModel):
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    monthly_limit: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    period: Optional[str] = Field(default=None, max_length=50)


class BudgetResponse(BudgetBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryBudgetStatusResponse(BaseModel):
    category: str
    monthly_limit: Decimal
    actual_spent: Decimal
    remaining_amount: Decimal
    percentage_consumed: Decimal
    variance: Decimal
    is_over_budget: bool
    status: str


class BudgetPerformanceResponse(BaseModel):
    total_budgeted: Decimal
    total_spent: Decimal
    total_remaining: Decimal
    overall_percentage_consumed: Decimal
    overall_variance: Decimal
    over_budget_count: int
    category_statuses: List[CategoryBudgetStatusResponse]
