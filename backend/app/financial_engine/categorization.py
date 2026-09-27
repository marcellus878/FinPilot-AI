from dataclasses import dataclass
import re
from typing import Optional, Tuple

# 14 Standard FinPilot Categories
VALID_CATEGORIES = [
    "Food",
    "Groceries",
    "Transport",
    "Shopping",
    "Entertainment",
    "Bills & Utilities",
    "Healthcare",
    "Education",
    "Rent/Housing",
    "EMI/Debt",
    "Salary/Income",
    "Savings/Investment",
    "Cash Withdrawal",
    "Miscellaneous",
]

# Merchant and Keyword Rules for Categorization
CATEGORY_KEYWORD_MAP = {
    "Food": [
        "swiggy", "zomato", "restaurant", "cafe", "coffee", "starbucks", "mcdonald", "kfc",
        "burger", "pizza", "domino", "subway", "bar", "pub", "bistro", "bakery", "diner",
        "lunch", "dinner", "breakfast", "eats", "doordash", "uber eats", "dineout", "food"
    ],
    "Groceries": [
        "grocery", "groceries", "supermarket", "blinkit", "zepto", "instamart", "bigbasket",
        "walmart", "trader joe", "target", "costco", "whole foods", "safeway", "aldi",
        "spencers", "dmart", "reliance fresh", "nature's basket", "vegetables", "fruits", "milk", "provision"
    ],
    "Transport": [
        "uber", "ola", "rapido", "cab", "taxi", "lyft", "metro", "bus", "train", "railway",
        "irctc", "flight", "indigo", "air india", "petrol", "diesel", "fuel", "gas station",
        "toll", "fastag", "parking", "auto", "airline", "commute", "shell", "hpcl", "bpcl", "ioc"
    ],
    "Shopping": [
        "amazon", "flipkart", "myntra", "ajio", "zara", "h&m", "nike", "adidas", "puma",
        "clothing", "apparel", "shoes", "electronics", "retail", "mall", "ebay", "etsy",
        "meesho", "nykaa", "sephora", "uniqlo", "best buy", "apple store", "croma", "reliance digital"
    ],
    "Entertainment": [
        "netflix", "spotify", "prime video", "disney", "hotstar", "youtube", "cinema", "movie",
        "pvr", "inox", "bookmyshow", "theatre", "concert", "game", "steam", "playstation",
        "xbox", "nintendo", "hulu", "apple tv", "gaming", "amusement", "club"
    ],
    "Bills & Utilities": [
        "airtel", "jio", "vi", "vodafone", "verizon", "at&t", "broadband", "wifi", "internet",
        "electricity", "power", "water", "gas bill", "utility", "bescom", "tneb", "mgl",
        "recharge", "mobile bill", "cable", "dth", "trash", "sewage"
    ],
    "Healthcare": [
        "pharmacy", "medicine", "hospital", "clinic", "doctor", "dentist", "medical",
        "1mg", "pharmeasy", "apollo", "medplus", "diagnostic", "lab", "health",
        "practo", "care", "wellness", "therapy", "dental", "optometry"
    ],
    "Education": [
        "school", "college", "university", "tuition", "course", "udemy", "coursera",
        "edx", "books", "stationery", "exam", "academy", "training", "class", "coaching"
    ],
    "Rent/Housing": [
        "rent", "landlord", "society", "maintenance", "apartment", "housing", "mortgage",
        "property tax", "hoa", "nobroker", "flat"
    ],
    "EMI/Debt": [
        "emi", "loan", "credit card payment", "hdfc bank loan", "sbi card", "icici loan",
        "bajaj finserv", "credo", "debt", "interest", "finance emi", "car loan", "home loan", "personal loan"
    ],
    "Salary/Income": [
        "salary", "payroll", "stipend", "bonus", "dividend", "interest credited",
        "freelance", "consulting fee", "refund", "cashback", "incentive", "wages"
    ],
    "Savings/Investment": [
        "zerodha", "groww", "upstox", "mutual fund", "sip", "stocks", "etf", "crypto",
        "coinbase", "binance", "fixed deposit", "recurring deposit", "ppf", "nps", "gold", "vanguard", "fidelity"
    ],
    "Cash Withdrawal": [
        "atm", "cash withdrawal", "atm wdl", "cash w/d", "self withdrawal"
    ],
}

@dataclass
class CategorizationResult:
    category: str
    confidence: float
    matched_rule: Optional[str] = None


@dataclass
class EssentialityResult:
    essentiality: str  # 'essential' | 'semi_essential' | 'discretionary'
    reason: str


def categorize_transaction(
    description: Optional[str],
    tx_type: str = "expense",
    explicit_category: Optional[str] = None,
) -> CategorizationResult:
    """
    Deterministic rule-based categorization engine.
    Matches merchant / description tokens to standard FinPilot categories.
    """
    if explicit_category and explicit_category in VALID_CATEGORIES:
        return CategorizationResult(
            category=explicit_category,
            confidence=1.0,
            matched_rule="user_explicit",
        )

    if tx_type == "income":
        return CategorizationResult(
            category="Salary/Income",
            confidence=0.9,
            matched_rule="default_income",
        )

    if not description:
        return CategorizationResult(
            category="Miscellaneous",
            confidence=0.3,
            matched_rule="no_description_fallback",
        )

    text = description.lower()

    # Exact and token-based keyword matching
    for cat, keywords in CATEGORY_KEYWORD_MAP.items():
        for kw in keywords:
            # Check for word boundary match or containment for specific brand names
            pattern = rf"(?:\b|_){re.escape(kw)}(?:\b|_)"
            if re.search(pattern, text) or kw in text:
                return CategorizationResult(
                    category=cat,
                    confidence=0.95 if kw in ["swiggy", "zomato", "uber", "ola", "amazon", "netflix", "airtel", "jio"] else 0.85,
                    matched_rule=f"keyword:{kw}",
                )

    return CategorizationResult(
        category="Miscellaneous",
        confidence=0.4,
        matched_rule="unmatched_fallback",
    )


def classify_essentiality(
    category: str,
    description: Optional[str] = None,
    tx_type: str = "expense",
) -> EssentialityResult:
    """
    Deterministic essential vs semi-essential vs discretionary classifier.
    Explains the rule and rationale used.
    """
    if tx_type == "income":
        return EssentialityResult(
            essentiality="essential",
            reason="Income inflow is a core financial resource requirement.",
        )

    cat = category.strip()
    text = (description or "").lower()

    # Category level & description refinement
    if cat in ["Rent/Housing", "EMI/Debt"]:
        return EssentialityResult(
            essentiality="essential",
            reason=f"{cat} represents fixed non-negotiable living and contractual commitments.",
        )

    if cat in ["Healthcare", "Bills & Utilities", "Education"]:
        return EssentialityResult(
            essentiality="essential",
            reason=f"{cat} constitutes fundamental survival, utility, and welfare services.",
        )

    if cat == "Groceries":
        # Grocery purchases are essential
        return EssentialityResult(
            essentiality="essential",
            reason="Basic groceries and provisions are essential nutritional necessities.",
        )

    if cat == "Food":
        # Check if restaurant delivery vs basic meals
        if any(d in text for d in ["swiggy", "zomato", "doordash", "uber eats", "bar", "pub", "brewery"]):
            return EssentialityResult(
                essentiality="discretionary",
                reason="Dining out and on-demand food delivery represent discretionary lifestyle spending.",
            )
        return EssentialityResult(
            essentiality="semi_essential",
            reason="Outside dining provides nutrition but can be optimized compared to home cooking.",
        )

    if cat == "Transport":
        if any(f in text for f in ["petrol", "diesel", "fuel", "metro", "bus", "train", "commute"]):
            return EssentialityResult(
                essentiality="essential",
                reason="Daily commute and essential vehicle fueling are necessary transportation needs.",
            )
        return EssentialityResult(
            essentiality="semi_essential",
            reason="On-demand ride-hailing (cabs/taxis) provides transit but carries discretionary premiums.",
        )

    if cat == "Shopping":
        if any(w in text for w in ["luxury", "jewel", "watch", "perfume", "fashion"]):
            return EssentialityResult(
                essentiality="discretionary",
                reason="Luxury and non-essential retail shopping are discretionary lifestyle choices.",
            )
        return EssentialityResult(
            essentiality="semi_essential",
            reason="General retail shopping may include necessary household apparel or goods.",
        )

    if cat == "Entertainment":
        return EssentialityResult(
            essentiality="discretionary",
            reason="Media streaming, cinema, gaming, and leisure activities are discretionary entertainment.",
        )

    if cat in ["Savings/Investment"]:
        return EssentialityResult(
            essentiality="essential",
            reason="Savings and systematic wealth accumulation support future financial security.",
        )

    if cat == "Cash Withdrawal":
        return EssentialityResult(
            essentiality="semi_essential",
            reason="Cash withdrawals can cover mixed essential and discretionary cash expenses.",
        )

    # Miscellaneous default
    return EssentialityResult(
        essentiality="discretionary",
        reason="Miscellaneous and uncategorized expenses default to discretionary until classified.",
    )
