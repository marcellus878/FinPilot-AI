from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional

from app.financial_engine.categorization import (
    categorize_transaction,
    classify_essentiality,
)

@dataclass
class SpendingPatternItem:
    pattern_type: str
    category: Optional[str]
    title: str
    description: str
    impact_level: str  # 'low' | 'medium' | 'high'
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SpendingHabitItem:
    habit_name: str
    category: str
    description: str
    frequency_per_month: int
    monthly_cost: Decimal
    severity: str  # 'info' | 'warning' | 'alert'
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecurringExpenseItem:
    merchant: str
    category: str
    approximate_amount: Decimal
    frequency: str  # 'weekly' | 'monthly' | 'quarterly' | 'annual'
    confidence: float
    occurrence_count: int
    last_occurrence: datetime
    next_expected_date: Optional[datetime]
    is_confirmed: bool = False
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HiddenExpenseItem:
    merchant: str
    category: str
    individual_amount: Decimal
    total_monthly_cost: Decimal
    occurrence_count: int
    discretionary_share_pct: Decimal
    annualized_cost: Decimal
    description: str


@dataclass
class MiscellaneousSpendingResult:
    total_miscellaneous_amount: Decimal
    percentage_of_expenses: Decimal
    transaction_count: int
    largest_miscellaneous_transactions: List[Dict[str, Any]]
    recurring_miscellaneous_merchants: List[Dict[str, Any]]
    leak_severity: str  # 'low' | 'medium' | 'high'
    description: str


@dataclass
class SpendingIntelligenceResult:
    essential_amount: Decimal
    semi_essential_amount: Decimal
    discretionary_amount: Decimal
    essential_percentage: Decimal
    semi_essential_percentage: Decimal
    discretionary_percentage: Decimal
    patterns: List[SpendingPatternItem]
    habits: List[SpendingHabitItem]
    recurring_expenses: List[RecurringExpenseItem]
    hidden_expenses: List[HiddenExpenseItem]
    miscellaneous_analysis: MiscellaneousSpendingResult


def normalize_merchant_name(description: str) -> str:
    """
    Cleans and normalizes merchant names for clustering.
    e.g. 'SWIGGY_1283912' -> 'Swiggy', 'AMZN MKTPLACE' -> 'Amazon'
    """
    if not description:
        return "Miscellaneous"

    text = description.upper()

    # Common brand normalizations
    known_brands = {
        "SWIGGY": "Swiggy",
        "ZOMATO": "Zomato",
        "UBER": "Uber",
        "OLA": "Ola",
        "AMAZON": "Amazon",
        "AMZN": "Amazon",
        "FLIPKART": "Flipkart",
        "NETFLIX": "Netflix",
        "SPOTIFY": "Spotify",
        "AIRTEL": "Airtel",
        "JIO": "Jio",
        "BLINKIT": "Blinkit",
        "ZEPTO": "Zepto",
        "STARBUCKS": "Starbucks",
        "PETROL": "Fuel / Petrol",
        "SHELL": "Shell Fuel",
        "HPCL": "HPCL Fuel",
        "BPCL": "BPCL Fuel",
        "IOCL": "IOCL Fuel",
        "BIGBASKET": "BigBasket",
        "DMART": "DMart",
        "WALMART": "Walmart",
        "TARGET": "Target",
        "COSTCO": "Costco",
        "CRED": "CRED Payment",
        "ACT": "ACT Broadband",
        "HDFCBANK": "HDFC Bank",
        "ICICIBANK": "ICICI Bank",
        "SBIBANK": "SBI Bank",
    }

    for key, normalized in known_brands.items():
        if key in text:
            return normalized

    # Strip transaction IDs, dates, and non-alphanumeric noise
    clean = re.sub(r"[\d\-_/]+", " ", description).strip()
    words = clean.split()
    if words:
        return " ".join(w.capitalize() for w in words[:3])
    return description.strip().capitalize()


def analyze_spending_patterns(transactions: List[Any]) -> List[SpendingPatternItem]:
    """
    Deterministic spending pattern analyzer.
    Detects weekend vs weekday ratio, concentration in top categories, average size, etc.
    """
    patterns: List[SpendingPatternItem] = []
    expense_txs = [t for t in transactions if getattr(t, "type", "").lower() == "expense"]

    if not expense_txs:
        return patterns

    total_expense = sum((Decimal(str(getattr(t, "amount", 0))) for t in expense_txs), Decimal("0.00"))
    if total_expense <= 0:
        return patterns

    # 1. Weekend vs Weekday analysis
    weekday_spend = Decimal("0.00")
    weekend_spend = Decimal("0.00")
    weekday_count = 0
    weekend_count = 0

    for tx in expense_txs:
        tx_d = getattr(tx, "transaction_date", None) or datetime.now()
        amt = Decimal(str(getattr(tx, "amount", 0)))
        # Monday=0 ... Sunday=6. Saturday(5) and Sunday(6) are weekend
        if tx_d.weekday() in (5, 6):
            weekend_spend += amt
            weekend_count += 1
        else:
            weekday_spend += amt
            weekday_count += 1

    weekend_pct = (weekend_spend / total_expense * Decimal("100.00")).quantize(Decimal("0.01")) if total_expense > 0 else Decimal("0.00")

    if weekend_pct >= Decimal("35.00"):  # Note: weekends are 2/7 (~28.5%) of days
        patterns.append(
            SpendingPatternItem(
                pattern_type="weekend_concentration",
                category="General",
                title="Elevated Weekend Spending",
                description=f"Weekend expenses account for {weekend_pct}% of total spending (${weekend_spend:,.2f}), exceeding typical weekday spending density.",
                impact_level="medium" if weekend_pct < Decimal("50.00") else "high",
                evidence={
                    "weekend_amount": str(weekend_spend),
                    "weekday_amount": str(weekday_spend),
                    "weekend_percentage": str(weekend_pct),
                    "weekend_tx_count": weekend_count,
                    "weekday_tx_count": weekday_count,
                },
            )
        )

    # 2. Spending Concentration in Top Categories
    cat_totals: Dict[str, Decimal] = defaultdict(Decimal)
    for tx in expense_txs:
        cat = getattr(tx, "category", "Miscellaneous")
        amt = Decimal(str(getattr(tx, "amount", 0)))
        cat_totals[cat] += amt

    sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
    if sorted_cats:
        top_cat, top_amt = sorted_cats[0]
        top_pct = (top_amt / total_expense * Decimal("100.00")).quantize(Decimal("0.01"))
        if top_pct >= Decimal("40.00"):
            patterns.append(
                SpendingPatternItem(
                    pattern_type="category_concentration",
                    category=top_cat,
                    title=f"High Concentration in {top_cat}",
                    description=f"{top_cat} makes up {top_pct}% (${top_amt:,.2f}) of all your monthly expenses.",
                    impact_level="high",
                    evidence={
                        "top_category": top_cat,
                        "amount": str(top_amt),
                        "percentage": str(top_pct),
                    },
                )
            )

    # 3. Average Transaction Size and Small Transaction Frequency
    avg_tx = (total_expense / Decimal(str(len(expense_txs)))).quantize(Decimal("0.01"))
    small_txs = [t for t in expense_txs if Decimal(str(getattr(t, "amount", 0))) <= Decimal("25.00")]
    small_pct = (Decimal(str(len(small_txs))) / Decimal(str(len(expense_txs))) * Decimal("100.00")).quantize(Decimal("0.01"))

    if small_pct >= Decimal("50.00"):
        patterns.append(
            SpendingPatternItem(
                pattern_type="high_frequency_micro_transactions",
                category="General",
                title="Frequent Micro-Transactions",
                description=f"{small_pct}% of your transactions ({len(small_txs)} transactions) are small amounts ($25.00 or under), averaging ${avg_tx} overall.",
                impact_level="low",
                evidence={
                    "small_tx_count": len(small_txs),
                    "total_tx_count": len(expense_txs),
                    "small_tx_percentage": str(small_pct),
                    "average_tx_amount": str(avg_tx),
                },
            )
        )

    return patterns


def detect_miscellaneous_spending(transactions: List[Any]) -> MiscellaneousSpendingResult:
    """
    Identifies untagged and miscellaneous spending leaks.
    """
    expense_txs = [t for t in transactions if getattr(t, "type", "").lower() == "expense"]
    total_expense = sum((Decimal(str(getattr(t, "amount", 0))) for t in expense_txs), Decimal("0.00"))

    misc_txs = [
        t for t in expense_txs
        if getattr(t, "category", "").lower() in ["miscellaneous", "other", "unknown", "uncategorized"]
    ]

    misc_amount = sum((Decimal(str(getattr(t, "amount", 0))) for t in misc_txs), Decimal("0.00"))
    misc_pct = (misc_amount / total_expense * Decimal("100.00")).quantize(Decimal("0.01")) if total_expense > 0 else Decimal("0.00")

    # Largest misc transactions
    sorted_misc = sorted(misc_txs, key=lambda x: Decimal(str(getattr(x, "amount", 0))), reverse=True)
    largest = [
        {
            "description": getattr(t, "description", "Unknown"),
            "amount": str(Decimal(str(getattr(t, "amount", 0)))),
            "date": getattr(t, "transaction_date", datetime.now()).strftime("%Y-%m-%d"),
        }
        for t in sorted_misc[:5]
    ]

    # Recurring misc merchants
    merchant_counts: Dict[str, int] = defaultdict(int)
    for t in misc_txs:
        desc = getattr(t, "description", None)
        if desc:
            merchant_counts[normalize_merchant_name(desc)] += 1

    recurring_merchants = [
        {"merchant": m, "count": cnt}
        for m, cnt in merchant_counts.items()
        if cnt >= 2
    ]

    severity = "low"
    if misc_pct >= Decimal("15.00") or misc_amount >= Decimal("500.00"):
        severity = "high"
    elif misc_pct >= Decimal("7.00") or misc_amount >= Decimal("200.00"):
        severity = "medium"

    desc = f"Miscellaneous spending is ${misc_amount:,.2f} ({misc_pct}% of total expenses) across {len(misc_txs)} transactions."

    return MiscellaneousSpendingResult(
        total_miscellaneous_amount=misc_amount,
        percentage_of_expenses=misc_pct,
        transaction_count=len(misc_txs),
        largest_miscellaneous_transactions=largest,
        recurring_miscellaneous_merchants=recurring_merchants,
        leak_severity=severity,
        description=desc,
    )


def detect_spending_habits(transactions: List[Any]) -> List[SpendingHabitItem]:
    """
    Detects behavioral spending habits from transaction history.
    """
    habits: List[SpendingHabitItem] = []
    expense_txs = [t for t in transactions if getattr(t, "type", "").lower() == "expense"]

    if not expense_txs:
        return habits

    # 1. Food Delivery Habit
    delivery_txs = [
        t for t in expense_txs
        if any(d in (getattr(t, "description", "") or "").lower() for d in ["swiggy", "zomato", "doordash", "uber eats"])
    ]
    if len(delivery_txs) >= 4:
        total_deliv = sum((Decimal(str(getattr(t, "amount", 0))) for t in delivery_txs), Decimal("0.00"))
        habits.append(
            SpendingHabitItem(
                habit_name="Frequent On-Demand Food Delivery",
                category="Food",
                description=f"Recorded {len(delivery_txs)} delivery orders totaling ${total_deliv:,.2f} this period.",
                frequency_per_month=len(delivery_txs),
                monthly_cost=total_deliv,
                severity="warning" if len(delivery_txs) >= 8 else "info",
                evidence={
                    "count": len(delivery_txs),
                    "total_cost": str(total_deliv),
                    "merchants": list(set(normalize_merchant_name(getattr(t, "description", "")) for t in delivery_txs)),
                },
            )
        )

    # 2. Coffee / Cafe Habit
    cafe_txs = [
        t for t in expense_txs
        if any(c in (getattr(t, "description", "") or "").lower() for c in ["starbucks", "cafe", "coffee", "blue tokai", "ccd", "dunkin"])
    ]
    if len(cafe_txs) >= 3:
        total_cafe = sum((Decimal(str(getattr(t, "amount", 0))) for t in cafe_txs), Decimal("0.00"))
        habits.append(
            SpendingHabitItem(
                habit_name="Regular Coffee & Cafe Visits",
                category="Food",
                description=f"{len(cafe_txs)} cafe/coffee purchases totaling ${total_cafe:,.2f}.",
                frequency_per_month=len(cafe_txs),
                monthly_cost=total_cafe,
                severity="info",
                evidence={"count": len(cafe_txs), "total_cost": str(total_cafe)},
            )
        )

    # 3. Frequent Ride Hailing
    rides = [
        t for t in expense_txs
        if any(r in (getattr(t, "description", "") or "").lower() for r in ["uber", "ola", "lyft", "rapido"])
    ]
    if len(rides) >= 5:
        total_rides = sum((Decimal(str(getattr(t, "amount", 0))) for t in rides), Decimal("0.00"))
        habits.append(
            SpendingHabitItem(
                habit_name="High-Frequency Ride Hailing",
                category="Transport",
                description=f"Used cab/auto services {len(rides)} times totaling ${total_rides:,.2f}.",
                frequency_per_month=len(rides),
                monthly_cost=total_rides,
                severity="warning" if total_rides >= Decimal("200.00") else "info",
                evidence={"count": len(rides), "total_cost": str(total_rides)},
            )
        )

    return habits


def detect_recurring_expenses(transactions: List[Any]) -> List[RecurringExpenseItem]:
    """
    Groups transactions by normalized merchant and identifies repeating cadences (weekly, monthly, quarterly).
    """
    recurring: List[RecurringExpenseItem] = []
    expense_txs = [t for t in transactions if getattr(t, "type", "").lower() == "expense"]

    merchant_groups: Dict[str, List[Any]] = defaultdict(list)
    for tx in expense_txs:
        desc = getattr(tx, "description", "") or getattr(tx, "category", "")
        norm = normalize_merchant_name(desc)
        merchant_groups[norm].append(tx)

    for merchant, tx_list in merchant_groups.items():
        if len(tx_list) < 2:
            continue

        # Sort chronologically
        sorted_txs = sorted(tx_list, key=lambda x: getattr(x, "transaction_date", datetime.now()))
        amounts = [Decimal(str(getattr(t, "amount", 0))) for t in sorted_txs]
        avg_amt = sum(amounts, Decimal("0.00")) / Decimal(str(len(amounts)))

        # Check intervals between dates
        dates = [getattr(t, "transaction_date", datetime.now()) for t in sorted_txs]
        intervals_days = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]

        if not intervals_days:
            continue

        avg_interval = sum(intervals_days) / len(intervals_days)
        last_date = dates[-1]

        frequency = "monthly"
        next_date: Optional[datetime] = None
        confidence = 0.70

        if 5 <= avg_interval <= 9:
            frequency = "weekly"
            next_date = last_date + timedelta(days=7)
            confidence = 0.85
        elif 25 <= avg_interval <= 35:
            frequency = "monthly"
            next_date = last_date + timedelta(days=30)
            confidence = 0.90
        elif 80 <= avg_interval <= 100:
            frequency = "quarterly"
            next_date = last_date + timedelta(days=90)
            confidence = 0.80
        else:
            # Check if amounts are identical (subscription like Netflix, broadband)
            if len(set(amounts)) == 1:
                frequency = "monthly"
                next_date = last_date + timedelta(days=30)
                confidence = 0.80
            else:
                continue

        cat = getattr(sorted_txs[0], "category", "Bills & Utilities")

        recurring.append(
            RecurringExpenseItem(
                merchant=merchant,
                category=cat,
                approximate_amount=avg_amt.quantize(Decimal("0.01")),
                frequency=frequency,
                confidence=confidence,
                occurrence_count=len(sorted_txs),
                last_occurrence=last_date,
                next_expected_date=next_date,
                is_confirmed=False,
                evidence={
                    "avg_interval_days": avg_interval,
                    "recorded_amounts": [str(a) for a in amounts],
                },
            )
        )

    return sorted(recurring, key=lambda r: r.approximate_amount, reverse=True)


def detect_hidden_expenses(
    transactions: List[Any],
    recurring_items: List[RecurringExpenseItem],
) -> List[HiddenExpenseItem]:
    """
    Detects small recurring charges (< $30 / ₹1,000) that individually look trivial
    but quietly drain funds when compounded monthly or annually.
    """
    hidden: List[HiddenExpenseItem] = []
    expense_txs = [t for t in transactions if getattr(t, "type", "").lower() == "expense"]
    total_expense = sum((Decimal(str(getattr(t, "amount", 0))) for t in expense_txs), Decimal("0.00"))

    # Small recurring charges (< $35)
    for rec in recurring_items:
        if rec.approximate_amount <= Decimal("35.00"):
            mult = Decimal("4.00") if rec.frequency == "weekly" else Decimal("1.00")
            monthly_cost = (rec.approximate_amount * mult).quantize(Decimal("0.01"))
            annual_cost = (monthly_cost * Decimal("12.00")).quantize(Decimal("0.01"))
            disc_share = (monthly_cost / total_expense * Decimal("100.00")).quantize(Decimal("0.01")) if total_expense > 0 else Decimal("0.00")

            hidden.append(
                HiddenExpenseItem(
                    merchant=rec.merchant,
                    category=rec.category,
                    individual_amount=rec.approximate_amount,
                    total_monthly_cost=monthly_cost,
                    occurrence_count=rec.occurrence_count,
                    discretionary_share_pct=disc_share,
                    annualized_cost=annual_cost,
                    description=f"{rec.merchant} costs ~${rec.approximate_amount:.2f} ({rec.frequency}), compounding to ${annual_cost:,.2f}/year.",
                )
            )

    return hidden


def calculate_spending_intelligence(
    transactions: List[Any],
) -> SpendingIntelligenceResult:
    """
    Unified Spending Intelligence Calculator.
    Computes essentiality breakdown, patterns, habits, recurring commitments,
    hidden expenses, and miscellaneous leak analysis.
    """
    expense_txs = [t for t in transactions if getattr(t, "type", "").lower() == "expense"]

    essential_amt = Decimal("0.00")
    semi_essential_amt = Decimal("0.00")
    discretionary_amt = Decimal("0.00")

    for tx in expense_txs:
        amt = Decimal(str(getattr(tx, "amount", 0)))
        cat = getattr(tx, "category", "Miscellaneous")
        desc = getattr(tx, "description", "")
        ess = classify_essentiality(category=cat, description=desc, tx_type="expense")

        if ess.essentiality == "essential":
            essential_amt += amt
        elif ess.essentiality == "semi_essential":
            semi_essential_amt += amt
        else:
            discretionary_amt += amt

    total_expense = essential_amt + semi_essential_amt + discretionary_amt

    ess_pct = (essential_amt / total_expense * Decimal("100.00")).quantize(Decimal("0.01")) if total_expense > 0 else Decimal("0.00")
    semi_pct = (semi_essential_amt / total_expense * Decimal("100.00")).quantize(Decimal("0.01")) if total_expense > 0 else Decimal("0.00")
    disc_pct = (discretionary_amt / total_expense * Decimal("100.00")).quantize(Decimal("0.01")) if total_expense > 0 else Decimal("0.00")

    patterns = analyze_spending_patterns(transactions)
    habits = detect_spending_habits(transactions)
    recurring = detect_recurring_expenses(transactions)
    hidden = detect_hidden_expenses(transactions, recurring)
    misc = detect_miscellaneous_spending(transactions)

    return SpendingIntelligenceResult(
        essential_amount=essential_amt.quantize(Decimal("0.01")),
        semi_essential_amount=semi_essential_amt.quantize(Decimal("0.01")),
        discretionary_amount=discretionary_amt.quantize(Decimal("0.01")),
        essential_percentage=ess_pct,
        semi_essential_percentage=semi_pct,
        discretionary_percentage=disc_pct,
        patterns=patterns,
        habits=habits,
        recurring_expenses=recurring,
        hidden_expenses=hidden,
        miscellaneous_analysis=misc,
    )
