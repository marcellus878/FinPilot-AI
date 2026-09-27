from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from decimal import Decimal
import re
from typing import List, Optional

from app.financial_engine.categorization import (
    categorize_transaction,
    classify_essentiality,
)

@dataclass
class ParsedTransaction:
    amount: Optional[Decimal]
    type: str  # 'expense' | 'income'
    category: str
    description: Optional[str]
    transaction_date: datetime
    essentiality: str
    essentiality_reason: str
    confidence: float
    raw_text: str
    missing_fields: List[str] = field(default_factory=list)


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

INCOME_KEYWORDS = [
    "got", "received", "salary", "credited", "earned", "refund", "cashback",
    "bonus", "dividend", "interest credited", "income", "freelance payment"
]

EXPENSE_KEYWORDS = [
    "spent", "paid", "bought", "gave", "sent", "ordered", "purchased",
    "debited", "charged", "withdrew", "cost", "bill", "emi"
]


def parse_natural_language_transaction(
    text: str,
    reference_date: Optional[datetime] = None,
) -> ParsedTransaction:
    """
    Deterministic NLP parser for single-sentence financial statements and speech transcripts.
    Extracts amount, type, date, merchant/description, and assigns category and essentiality.
    """
    if not reference_date:
        reference_date = datetime.now()

    raw_text = text.strip()
    clean_text = raw_text.lower()

    # 1. Parse Transaction Type
    tx_type = "expense"
    income_match = any(re.search(rf"\b{re.escape(w)}\b", clean_text) for w in INCOME_KEYWORDS)
    expense_match = any(re.search(rf"\b{re.escape(w)}\b", clean_text) for w in EXPENSE_KEYWORDS)

    if income_match and not expense_match:
        tx_type = "income"
    elif "salary" in clean_text or "dividend" in clean_text or "credited" in clean_text:
        tx_type = "income"

    # 2. Parse Amount
    amount = None
    # Match patterns like ₹450, $1,200.50, 450 rupees, rs 450, 450 bucks, 1.5k, 10k, 500.00
    amount_patterns = [
        # ₹ 450 / $ 1.5k / rs. 450 / inr 450
        r"(?:₹|rs\.?|inr|\$)\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?k?\b)",
        # 450 rupees / 450 bucks / 450 dollars / 450 usd / 450 inr / 1.5k rupees
        r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?k?)\s*(?:rupees|rupee|bucks|dollars|dollar|usd|inr|rs\.?)",
        # standalone decimal or integer with context: "for 450", "of 450", "spent 1.5k"
        r"(?:spent|paid|got|received|of|for|cost|amounting\s+to)\s*(?:₹|rs\.?|inr|\$)?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?k?\b)",
        # generic number pattern as fallback
        r"\b([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{1,2})?k?)\b",
    ]

    for pat in amount_patterns:
        m = re.search(pat, clean_text)
        if m:
            val_str = m.group(1).replace(",", "")
            if val_str.endswith("k"):
                try:
                    num = float(val_str[:-1]) * 1000
                    amount = Decimal(str(round(num, 2)))
                    break
                except ValueError:
                    pass
            else:
                try:
                    num = float(val_str)
                    if num > 0:
                        amount = Decimal(str(round(num, 2)))
                        break
                except ValueError:
                    pass

    # 3. Parse Date
    tx_date = reference_date

    if "day before yesterday" in clean_text:
        tx_date = reference_date - timedelta(days=2)
    elif "yesterday" in clean_text:
        tx_date = reference_date - timedelta(days=1)
    elif "today" in clean_text:
        tx_date = reference_date
    else:
        # Check for "last <weekday>"
        matched_weekday = False
        for day_name, day_idx in WEEKDAYS.items():
            if f"last {day_name}" in clean_text or f"on {day_name}" in clean_text:
                current_weekday = reference_date.weekday()
                days_ago = (current_weekday - day_idx) % 7
                if days_ago == 0:
                    days_ago = 7  # If same day, "last friday" refers to last week's friday
                tx_date = reference_date - timedelta(days=days_ago)
                matched_weekday = True
                break

        if not matched_weekday:
            # Check for explicit date like "on 12th march", "on 15-03-2026", "2026-03-12"
            iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", clean_text)
            if iso_match:
                try:
                    parsed_d = datetime.strptime(iso_match.group(1), "%Y-%m-%d")
                    tx_date = parsed_d
                except ValueError:
                    pass

    # 4. Extract Merchant / Description / Entities
    description = None

    # Patterns to pull entity after prepositions
    # e.g., "on Swiggy for dinner", "for petrol", "from TCS", "at Starbucks"
    prep_match = re.search(
        r"(?:on|at|for|from|to|via)\s+([a-zA-Z0-9\s'&]+?)(?:\s+(?:yesterday|today|last|on|\d{1,2}|for|rupees|rs|\$)|$)",
        raw_text,
        re.IGNORECASE,
    )
    if prep_match:
        candidate = prep_match.group(1).strip()
        # Filter out common stop words
        if candidate.lower() not in ["the", "a", "an", "my", "our", "him", "her", "me", "this", "that"]:
            description = candidate

    if not description:
        # Check known brands / keywords directly in text
        for kw_list in [
            ["swiggy", "zomato", "uber", "ola", "amazon", "flipkart", "netflix", "airtel", "jio", "blinkit", "zepto", "starbucks", "petrol", "groceries", "salary", "rent", "broadband", "electricity", "dinner", "lunch"]
        ]:
            for kw in kw_list:
                if re.search(rf"\b{re.escape(kw)}\b", clean_text):
                    description = kw.capitalize()
                    break

    if not description:
        description = raw_text

    # 5. Categorization and Essentiality
    cat_res = categorize_transaction(description=description or raw_text, tx_type=tx_type)
    category = cat_res.category

    ess_res = classify_essentiality(category=category, description=description, tx_type=tx_type)

    # 6. Assess Confidence and Missing Fields
    missing_fields = []
    if amount is None:
        missing_fields.append("amount")
    if not description or description == raw_text:
        missing_fields.append("description")

    confidence = 0.95
    if amount is None:
        confidence -= 0.4
    if cat_res.confidence < 0.6:
        confidence -= 0.2
    if not description:
        confidence -= 0.15

    confidence = max(0.1, min(1.0, round(confidence, 2)))

    return ParsedTransaction(
        amount=amount,
        type=tx_type,
        category=category,
        description=description,
        transaction_date=tx_date,
        essentiality=ess_res.essentiality,
        essentiality_reason=ess_res.reason,
        confidence=confidence,
        raw_text=raw_text,
        missing_fields=missing_fields,
    )
