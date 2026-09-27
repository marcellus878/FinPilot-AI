from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RecurringFrequencyType = Literal["weekly", "monthly", "quarterly", "annual"]
SurvivalStatusType = Literal["comfortable", "watch", "at_risk", "insufficient_data"]


class SalaryProfileBase(BaseModel):
    monthly_income: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Primary monthly net income")
    expected_salary_day: int = Field(default=1, ge=1, le=31, description="Day of month when salary is credited")
    additional_recurring_income: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Additional monthly income")
    savings_target: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), description="Target monthly savings")
    essential_spending_allowance: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), description="Essential spending allowance")
    discretionary_allowance: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"), description="Discretionary spending allowance")


class SalaryProfileCreate(SalaryProfileBase):
    pass


class SalaryProfileUpdate(BaseModel):
    monthly_income: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    expected_salary_day: Optional[int] = Field(default=None, ge=1, le=31)
    additional_recurring_income: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    savings_target: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    essential_spending_allowance: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    discretionary_allowance: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))


class SalaryProfileResponse(SalaryProfileBase):
    total_monthly_income: Decimal
    cycle_start_date: datetime
    next_salary_date: datetime
    days_in_cycle: int
    days_elapsed: int
    days_remaining: int


class RecurringCommitmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Merchant or commitment name")
    category: str = Field(default="Bills & Utilities", min_length=1, max_length=100)
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Payment amount")
    frequency: RecurringFrequencyType = Field(default="monthly", description="Payment cadence")
    next_expected_date: Optional[datetime] = None
    description: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_confirmed: bool = Field(default=True)


class RecurringCommitmentCreate(RecurringCommitmentBase):
    pass


class RecurringCommitmentUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    amount: Optional[Decimal] = Field(default=None, gt=Decimal("0.00"))
    frequency: Optional[RecurringFrequencyType] = None
    next_expected_date: Optional[datetime] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_confirmed: Optional[bool] = None


class RecurringCommitmentResponse(RecurringCommitmentBase):
    id: str
    monthly_equivalent: Decimal
    is_due_in_current_cycle: bool


class AllocationAlternativeResponse(BaseModel):
    title: str
    description: str
    adjusted_savings_target: Decimal
    adjusted_essential_allowance: Decimal
    adjusted_discretionary_allowance: Decimal
    resulting_buffer: Decimal


class SalaryAllocationCalculateRequest(BaseModel):
    monthly_income: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    fixed_commitments: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    essential_allowance: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    savings_target: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    discretionary_allowance: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))


class SalaryAllocationResponse(BaseModel):
    monthly_income: Decimal
    fixed_commitments: Decimal
    essential_allowance: Decimal
    savings_target: Decimal
    discretionary_allowance: Decimal
    remaining_buffer: Decimal
    fixed_percentage: Decimal
    essential_percentage: Decimal
    savings_percentage: Decimal
    discretionary_percentage: Decimal
    buffer_percentage: Decimal
    is_feasible: bool
    deficit_amount: Decimal
    explanation: str
    alternatives: List[AllocationAlternativeResponse] = []


class SafeToSpendResponse(BaseModel):
    current_available_funds: Decimal
    upcoming_commitments: Decimal
    remaining_essential_allowance: Decimal
    savings_reserve: Decimal
    emergency_reserve: Decimal
    total_committed_and_reserved: Decimal
    safe_to_spend_amount: Decimal
    daily_safe_to_spend: Decimal
    days_remaining: int
    explanation: str


class SurvivalProjectionResponse(BaseModel):
    current_available_funds: Decimal
    recent_average_daily_burn: Decimal
    days_remaining: int
    upcoming_commitments: Decimal
    projected_remaining_spend: Decimal
    projected_end_of_month_balance: Decimal
    daily_spending_capacity: Decimal
    status: SurvivalStatusType
    explanation: str
    evidence: Dict[str, Any] = {}


class MonthlyFinancialPlanResponse(BaseModel):
    id: UUID
    user_id: UUID
    is_active: bool
    salary_profile: SalaryProfileResponse
    recurring_commitments: List[RecurringCommitmentResponse]
    allocation: SalaryAllocationResponse
    safe_to_spend: SafeToSpendResponse
    survival_projection: SurvivalProjectionResponse
    created_at: datetime
    updated_at: datetime
