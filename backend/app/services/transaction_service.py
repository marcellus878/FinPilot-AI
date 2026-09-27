from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.financial_engine import (
    calculate_category_breakdown,
    calculate_expense_summary,
    calculate_spending_intelligence,
    detect_hidden_expenses,
    detect_miscellaneous_spending,
    detect_recurring_expenses,
    detect_spending_habits,
    parse_natural_language_transaction,
    analyze_spending_patterns,
)
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.schemas.transaction import (
    CategorySpendingResponse,
    ExpenseSummaryResponse,
    HiddenExpenseResponse,
    MiscellaneousSpendingResponse,
    MonthOverMonthResponse,
    NLParseResponse,
    RecurringExpenseResponse,
    SpendingFlagResponse,
    SpendingHabitResponse,
    SpendingIntelligenceResponse,
    SpendingPatternResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)


def parse_transaction_text(
    text: str,
    reference_date: Optional[datetime] = None,
) -> NLParseResponse:
    parsed = parse_natural_language_transaction(text=text, reference_date=reference_date)
    return NLParseResponse(
        amount=parsed.amount,
        type=parsed.type,  # type: ignore
        category=parsed.category,
        description=parsed.description,
        transaction_date=parsed.transaction_date,
        essentiality=parsed.essentiality,  # type: ignore
        essentiality_reason=parsed.essentiality_reason,
        confidence=parsed.confidence,
        raw_text=parsed.raw_text,
        missing_fields=parsed.missing_fields,
    )


def create_transaction(
    db: Session,
    user_id: UUID,
    tx_in: TransactionCreate,
) -> Transaction:
    tx = Transaction(
        user_id=user_id,
        amount=tx_in.amount,
        type=tx_in.type.lower(),
        category=tx_in.category.strip(),
        description=tx_in.description.strip() if tx_in.description else None,
        transaction_date=tx_in.transaction_date,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def get_transaction(
    db: Session,
    user_id: UUID,
    transaction_id: UUID,
) -> Optional[Transaction]:
    return (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == user_id)
        .first()
    )


def list_transactions(
    db: Session,
    user_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    category: Optional[str] = None,
    tx_type: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> List[Transaction]:
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if category:
        query = query.filter(Transaction.category.ilike(f"%{category.strip()}%"))
    if tx_type:
        query = query.filter(Transaction.type == tx_type.lower())

    return query.order_by(desc(Transaction.transaction_date)).offset(offset).limit(limit).all()


def update_transaction(
    db: Session,
    user_id: UUID,
    transaction_id: UUID,
    tx_in: TransactionUpdate,
) -> Optional[Transaction]:
    tx = get_transaction(db, user_id, transaction_id)
    if not tx:
        return None

    data = tx_in.model_dump(exclude_unset=True)
    for key, val in data.items():
        if val is not None:
            if key == "type":
                setattr(tx, key, str(val).lower())
            elif key == "category":
                setattr(tx, key, str(val).strip())
            elif key == "description":
                setattr(tx, key, str(val).strip() if val else None)
            else:
                setattr(tx, key, val)

    db.commit()
    db.refresh(tx)
    return tx


def delete_transaction(
    db: Session,
    user_id: UUID,
    transaction_id: UUID,
) -> bool:
    tx = get_transaction(db, user_id, transaction_id)
    if not tx:
        return False
    db.delete(tx)
    db.commit()
    return True


def get_user_expense_summary(
    db: Session,
    user_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> ExpenseSummaryResponse:
    now = datetime.now()
    if not start_date:
        start_date = datetime(now.year, now.month, 1)
    if not end_date:
        end_date = now

    current_txs = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        .all()
    )

    period_days = max(1, (end_date - start_date).days)
    prev_end = start_date
    prev_start = start_date - timedelta(days=period_days)
    prev_txs = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_date >= prev_start,
            Transaction.transaction_date < prev_end,
        )
        .all()
    )

    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()

    summary_result = calculate_expense_summary(
        transactions=current_txs,
        previous_period_transactions=prev_txs,
        budgets=budgets,
    )

    mom_resp = (
        MonthOverMonthResponse(
            previous_total_expenses=summary_result.month_over_month.previous_total_expenses,
            current_total_expenses=summary_result.month_over_month.current_total_expenses,
            delta_amount=summary_result.month_over_month.delta_amount,
            delta_percentage=summary_result.month_over_month.delta_percentage,
            trend=summary_result.month_over_month.trend,
        )
        if summary_result.month_over_month
        else None
    )

    cat_resp = [
        CategorySpendingResponse(
            category=c.category,
            total_amount=c.total_amount,
            percentage_of_total=c.percentage_of_total,
            transaction_count=c.transaction_count,
            is_essential=c.is_essential,
        )
        for c in summary_result.category_breakdown
    ]

    largest_resp = [
        CategorySpendingResponse(
            category=c.category,
            total_amount=c.total_amount,
            percentage_of_total=c.percentage_of_total,
            transaction_count=c.transaction_count,
            is_essential=c.is_essential,
        )
        for c in summary_result.largest_categories
    ]

    flags_resp = [
        SpendingFlagResponse(
            flag_type=f.flag_type,
            severity=f.severity,
            category=f.category,
            description=f.description,
            amount=f.amount,
            threshold=f.threshold,
        )
        for f in summary_result.spending_flags
    ]

    return ExpenseSummaryResponse(
        total_income=summary_result.total_income,
        total_expenses=summary_result.total_expenses,
        net_savings=summary_result.net_savings,
        savings_rate=summary_result.savings_rate,
        essential_spending=summary_result.essential_spending,
        non_essential_spending=summary_result.non_essential_spending,
        essential_percentage=summary_result.essential_percentage,
        non_essential_percentage=summary_result.non_essential_percentage,
        transaction_count=summary_result.transaction_count,
        income_transaction_count=summary_result.income_transaction_count,
        expense_transaction_count=summary_result.expense_transaction_count,
        month_over_month=mom_resp,
        category_breakdown=cat_resp,
        largest_categories=largest_resp,
        spending_flags=flags_resp,
    )


def get_user_category_spending(
    db: Session,
    user_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[CategorySpendingResponse]:
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    txs = query.all()
    items = calculate_category_breakdown(txs)
    return [
        CategorySpendingResponse(
            category=c.category,
            total_amount=c.total_amount,
            percentage_of_total=c.percentage_of_total,
            transaction_count=c.transaction_count,
            is_essential=c.is_essential,
        )
        for c in items
    ]


def get_user_spending_intelligence(
    db: Session,
    user_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> SpendingIntelligenceResponse:
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    txs = query.all()
    intel = calculate_spending_intelligence(txs)

    pattern_res = [
        SpendingPatternResponse(
            pattern_type=p.pattern_type,
            category=p.category,
            title=p.title,
            description=p.description,
            impact_level=p.impact_level,
            evidence=p.evidence,
        )
        for p in intel.patterns
    ]

    habit_res = [
        SpendingHabitResponse(
            habit_name=h.habit_name,
            category=h.category,
            description=h.description,
            frequency_per_month=h.frequency_per_month,
            monthly_cost=h.monthly_cost,
            severity=h.severity,
            evidence=h.evidence,
        )
        for h in intel.habits
    ]

    rec_res = [
        RecurringExpenseResponse(
            merchant=r.merchant,
            category=r.category,
            approximate_amount=r.approximate_amount,
            frequency=r.frequency,
            confidence=r.confidence,
            occurrence_count=r.occurrence_count,
            last_occurrence=r.last_occurrence,
            next_expected_date=r.next_expected_date,
            is_confirmed=r.is_confirmed,
            evidence=r.evidence,
        )
        for r in intel.recurring_expenses
    ]

    hidden_res = [
        HiddenExpenseResponse(
            merchant=hd.merchant,
            category=hd.category,
            individual_amount=hd.individual_amount,
            total_monthly_cost=hd.total_monthly_cost,
            occurrence_count=hd.occurrence_count,
            discretionary_share_pct=hd.discretionary_share_pct,
            annualized_cost=hd.annualized_cost,
            description=hd.description,
        )
        for hd in intel.hidden_expenses
    ]

    misc_res = MiscellaneousSpendingResponse(
        total_miscellaneous_amount=intel.miscellaneous_analysis.total_miscellaneous_amount,
        percentage_of_expenses=intel.miscellaneous_analysis.percentage_of_expenses,
        transaction_count=intel.miscellaneous_analysis.transaction_count,
        largest_miscellaneous_transactions=intel.miscellaneous_analysis.largest_miscellaneous_transactions,
        recurring_miscellaneous_merchants=intel.miscellaneous_analysis.recurring_miscellaneous_merchants,
        leak_severity=intel.miscellaneous_analysis.leak_severity,
        description=intel.miscellaneous_analysis.description,
    )

    return SpendingIntelligenceResponse(
        essential_amount=intel.essential_amount,
        semi_essential_amount=intel.semi_essential_amount,
        discretionary_amount=intel.discretionary_amount,
        essential_percentage=intel.essential_percentage,
        semi_essential_percentage=intel.semi_essential_percentage,
        discretionary_percentage=intel.discretionary_percentage,
        patterns=pattern_res,
        habits=habit_res,
        recurring_expenses=rec_res,
        hidden_expenses=hidden_res,
        miscellaneous_analysis=misc_res,
    )
