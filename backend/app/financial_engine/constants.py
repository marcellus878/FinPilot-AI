from decimal import Decimal

DECIMAL_ZERO = Decimal("0.00")
DECIMAL_ONE_HUNDRED = Decimal("100.00")
CURRENCY_QUANTIZATION = Decimal("0.01")
PERCENTAGE_QUANTIZATION = Decimal("0.01")

DEFAULT_EMERGENCY_MONTHS = Decimal("6.00")
MIN_EMERGENCY_MONTHS = Decimal("3.00")

DEFAULT_HEALTH_WEIGHTS = {
    "savings_rate": Decimal("0.25"),
    "debt_to_income": Decimal("0.25"),
    "emergency_fund": Decimal("0.20"),
    "budget_discipline": Decimal("0.15"),
    "goal_progress": Decimal("0.15"),
}

PRIORITY_RANKS = {
    "high": 1,
    "medium": 2,
    "low": 3,
}
