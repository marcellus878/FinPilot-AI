from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TransactionType = Literal["income", "expense"]
EssentialityType = Literal["essential", "semi_essential", "discretionary"]


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0.00"), description="Transaction amount (must be positive)")
    type: TransactionType = Field(..., description="Transaction type: income or expense")
    category: str = Field(..., min_length=1, max_length=100, description="Spending or income category")
    description: Optional[str] = Field(default=None, max_length=255, description="Description or merchant name")
    transaction_date: datetime = Field(..., description="Date and time of the transaction")


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Optional[Decimal] = Field(default=None, gt=Decimal("0.00"))
    type: Optional[TransactionType] = None
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    transaction_date: Optional[datetime] = None


class TransactionResponse(TransactionBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Natural Language & Voice Parsing Schemas
class NLParseRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, description="Natural language or speech transcript")
    reference_date: Optional[datetime] = Field(default=None, description="Optional reference date for relative parsing")


class NLParseResponse(BaseModel):
    amount: Optional[Decimal] = None
    type: TransactionType = "expense"
    category: str
    description: Optional[str] = None
    transaction_date: datetime
    essentiality: EssentialityType
    essentiality_reason: str
    confidence: float
    raw_text: str
    missing_fields: List[str] = []


# Statement Ingestion Schemas
class StatementRowPreview(BaseModel):
    row_index: int
    transaction_date: datetime
    amount: Decimal
    type: TransactionType
    category: str
    description: str
    essentiality: EssentialityType
    essentiality_reason: str
    fingerprint: str
    is_duplicate: bool
    is_valid: bool
    error_message: Optional[str] = None


class StatementImportPreviewResponse(BaseModel):
    filename: str
    file_type: str
    total_rows: int
    valid_count: int
    duplicate_count: int
    skipped_count: int
    detected_columns: Dict[str, str]
    transactions: List[StatementRowPreview]
    errors: List[str] = []


class StatementImportConfirmItem(BaseModel):
    transaction_date: datetime
    amount: Decimal = Field(..., gt=Decimal("0.00"))
    type: TransactionType
    category: str
    description: Optional[str] = None
    fingerprint: Optional[str] = None


class StatementImportConfirmRequest(BaseModel):
    transactions: List[StatementImportConfirmItem]


class StatementImportConfirmResponse(BaseModel):
    imported_count: int
    skipped_duplicates_count: int
    transactions: List[TransactionResponse]


# Spending Intelligence Schemas
class CategorySpendingResponse(BaseModel):
    category: str
    total_amount: Decimal
    percentage_of_total: Decimal
    transaction_count: int
    is_essential: bool


class SpendingFlagResponse(BaseModel):
    flag_type: str
    severity: str
    category: str
    description: str
    amount: Decimal
    threshold: Decimal


class MonthOverMonthResponse(BaseModel):
    previous_total_expenses: Decimal
    current_total_expenses: Decimal
    delta_amount: Decimal
    delta_percentage: Decimal
    trend: str


class ExpenseSummaryResponse(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_savings: Decimal
    savings_rate: Decimal
    essential_spending: Decimal
    non_essential_spending: Decimal
    essential_percentage: Decimal
    non_essential_percentage: Decimal
    transaction_count: int
    income_transaction_count: int
    expense_transaction_count: int
    month_over_month: Optional[MonthOverMonthResponse]
    category_breakdown: List[CategorySpendingResponse]
    largest_categories: List[CategorySpendingResponse]
    spending_flags: List[SpendingFlagResponse]


class SpendingPatternResponse(BaseModel):
    pattern_type: str
    category: Optional[str] = None
    title: str
    description: str
    impact_level: str
    evidence: Dict[str, Any] = {}


class SpendingHabitResponse(BaseModel):
    habit_name: str
    category: str
    description: str
    frequency_per_month: int
    monthly_cost: Decimal
    severity: str
    evidence: Dict[str, Any] = {}


class RecurringExpenseResponse(BaseModel):
    merchant: str
    category: str
    approximate_amount: Decimal
    frequency: str
    confidence: float
    occurrence_count: int
    last_occurrence: datetime
    next_expected_date: Optional[datetime] = None
    is_confirmed: bool = False
    evidence: Dict[str, Any] = {}


class HiddenExpenseResponse(BaseModel):
    merchant: str
    category: str
    individual_amount: Decimal
    total_monthly_cost: Decimal
    occurrence_count: int
    discretionary_share_pct: Decimal
    annualized_cost: Decimal
    description: str


class MiscellaneousSpendingResponse(BaseModel):
    total_miscellaneous_amount: Decimal
    percentage_of_expenses: Decimal
    transaction_count: int
    largest_miscellaneous_transactions: List[Dict[str, Any]]
    recurring_miscellaneous_merchants: List[Dict[str, Any]]
    leak_severity: str
    description: str


class SpendingIntelligenceResponse(BaseModel):
    essential_amount: Decimal
    semi_essential_amount: Decimal
    discretionary_amount: Decimal
    essential_percentage: Decimal
    semi_essential_percentage: Decimal
    discretionary_percentage: Decimal
    patterns: List[SpendingPatternResponse]
    habits: List[SpendingHabitResponse]
    recurring_expenses: List[RecurringExpenseResponse]
    hidden_expenses: List[HiddenExpenseResponse]
    miscellaneous_analysis: MiscellaneousSpendingResponse
