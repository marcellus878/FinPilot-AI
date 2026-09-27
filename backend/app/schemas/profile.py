from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RiskPreference = Literal["conservative", "moderate", "aggressive"]


class FinancialProfileBase(BaseModel):
    monthly_income: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Monthly gross/net income")
    current_savings: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Total liquid savings")
    monthly_debt_payment: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Total monthly debt payments")
    essential_expenses: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Essential monthly living expenses")
    dependents: int = Field(default=0, ge=0, description="Number of dependents")
    emergency_savings: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"), description="Designated emergency fund savings")
    risk_preference: RiskPreference = Field(default="moderate", description="Investment/financial risk profile")


class FinancialProfileCreate(FinancialProfileBase):
    pass


class FinancialProfileUpdate(BaseModel):
    monthly_income: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    current_savings: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    monthly_debt_payment: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    essential_expenses: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    dependents: Optional[int] = Field(default=None, ge=0)
    emergency_savings: Optional[Decimal] = Field(default=None, ge=Decimal("0.00"))
    risk_preference: Optional[RiskPreference] = None


class EmergencyFundIndicator(BaseModel):
    months_covered: Decimal
    target_months: Decimal
    target_amount: Decimal
    shortfall: Decimal
    surplus: Decimal
    is_adequate: bool
    status_label: str


class DerivedFinancialIndicators(BaseModel):
    disposable_income: Decimal
    savings_rate: Decimal
    expense_ratio: Decimal
    debt_to_income_ratio: Decimal
    emergency_fund: EmergencyFundIndicator
    financial_health_score: Decimal
    financial_health_grade: str


class FinancialProfileResponse(FinancialProfileBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    indicators: DerivedFinancialIndicators

    model_config = ConfigDict(from_attributes=True)
