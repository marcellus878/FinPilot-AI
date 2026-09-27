from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Union
from app.financial_engine.constants import (
    CURRENCY_QUANTIZATION,
    DECIMAL_ZERO,
    PERCENTAGE_QUANTIZATION,
)

def to_decimal(
    value: Union[int, float, str, Decimal],
    allow_negative: bool = True,
    name: str = "value",
) -> Decimal:
    if value is None:
        raise ValueError(f"{name} cannot be None")
    try:
        if isinstance(value, float):
            d = Decimal(str(value))
        else:
            d = Decimal(value)
    except (InvalidOperation, TypeError) as e:
        raise ValueError(f"Invalid monetary value for {name}: {value}") from e

    if not allow_negative and d < DECIMAL_ZERO:
        raise ValueError(f"{name} cannot be negative (got {d})")

    return d

def quantize_currency(value: Decimal) -> Decimal:
    return value.quantize(CURRENCY_QUANTIZATION, rounding=ROUND_HALF_UP)

def quantize_percentage(value: Decimal) -> Decimal:
    return value.quantize(PERCENTAGE_QUANTIZATION, rounding=ROUND_HALF_UP)

def safe_divide(
    numerator: Decimal,
    denominator: Decimal,
    default: Decimal = DECIMAL_ZERO,
) -> Decimal:
    if denominator == DECIMAL_ZERO or denominator is None:
        return default
    return numerator / denominator
