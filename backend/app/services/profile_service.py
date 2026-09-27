import uuid
from decimal import Decimal
from typing import Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from app.financial_engine import (
    calculate_debt_to_income_ratio,
    calculate_disposable_income,
    calculate_emergency_fund_status,
    calculate_expense_ratio,
    calculate_financial_health_score,
    calculate_savings_rate,
)
from app.models.financial_profile import FinancialProfile
from app.schemas.profile import (
    DerivedFinancialIndicators,
    EmergencyFundIndicator,
    FinancialProfileCreate,
    FinancialProfileResponse,
    FinancialProfileUpdate,
)


def calculate_profile_indicators(profile: FinancialProfile) -> DerivedFinancialIndicators:
    income = profile.monthly_income or Decimal("0.00")
    savings = profile.current_savings or Decimal("0.00")
    debt = profile.monthly_debt_payment or Decimal("0.00")
    essential = profile.essential_expenses or Decimal("0.00")
    emergency = profile.emergency_savings if profile.emergency_savings > Decimal("0.00") else savings

    disp = calculate_disposable_income(income, essential, debt)
    sav_rate = calculate_savings_rate(disp, income)
    exp_ratio = calculate_expense_ratio(essential, income)
    dti = calculate_debt_to_income_ratio(debt, income)
    ef_result = calculate_emergency_fund_status(emergency, essential)
    health_result = calculate_financial_health_score(income, essential, debt, savings)

    ef_indicator = EmergencyFundIndicator(
        months_covered=ef_result.months_covered,
        target_months=ef_result.target_months,
        target_amount=ef_result.target_amount,
        shortfall=ef_result.shortfall,
        surplus=ef_result.surplus,
        is_adequate=ef_result.is_adequate,
        status_label=ef_result.status_label,
    )

    return DerivedFinancialIndicators(
        disposable_income=disp,
        savings_rate=sav_rate,
        expense_ratio=exp_ratio,
        debt_to_income_ratio=dti,
        emergency_fund=ef_indicator,
        financial_health_score=health_result.overall_score,
        financial_health_grade=health_result.grade,
    )


def build_profile_response(profile: FinancialProfile) -> FinancialProfileResponse:
    indicators = calculate_profile_indicators(profile)
    return FinancialProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        monthly_income=profile.monthly_income,
        current_savings=profile.current_savings,
        monthly_debt_payment=profile.monthly_debt_payment,
        essential_expenses=profile.essential_expenses,
        dependents=profile.dependents,
        emergency_savings=profile.emergency_savings,
        risk_preference=profile.risk_preference,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        indicators=indicators,
    )


def get_profile_by_user(db: Session, user_id: UUID) -> Optional[FinancialProfile]:
    return db.query(FinancialProfile).filter(FinancialProfile.user_id == user_id).first()


def create_or_update_user_profile(
    db: Session,
    user_id: UUID,
    profile_data: Union[FinancialProfileCreate, FinancialProfileUpdate],
) -> FinancialProfile:
    profile = get_profile_by_user(db, user_id)
    data_dict = profile_data.model_dump(exclude_unset=True)

    if not profile:
        profile = FinancialProfile(
            user_id=user_id,
            **data_dict,
        )
        db.add(profile)
    else:
        for key, val in data_dict.items():
            if val is not None:
                setattr(profile, key, val)

    db.commit()
    db.refresh(profile)
    return profile
