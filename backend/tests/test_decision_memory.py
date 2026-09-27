import uuid
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.schemas.decision_memory import DecisionMemoryCreateSchema
from app.services.decision_memory_service import (
    evaluate_memory_drift,
    generate_proactive_insights,
    retrieve_relevant_memory,
    save_decision_memory,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email="test_memory@finpilot.ai",
        full_name="Decision Memory User",
    )
    db_session.add(user)
    db_session.commit()

    profile = FinancialProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        monthly_income=Decimal("6000.00"),
        current_savings=Decimal("15000.00"),
        monthly_debt_payment=Decimal("400.00"),
        essential_expenses=Decimal("2800.00"),
        emergency_savings=Decimal("12000.00"),
        dependents=1,
        risk_preference="moderate",
    )
    db_session.add(profile)
    db_session.commit()
    return user


class TestDecisionMemory:
    def test_01_save_and_retrieve_decision_memory(self, db_session, sample_user):
        data = DecisionMemoryCreateSchema(
            user_action="Can I afford to buy a $2,500 gaming laptop?",
            decision="Verdict: AFFORDABLE_WITH_TRADE_OFFS — Recommended: Delay 2 months to protect emergency fund",
            decision_type="large_purchase",
            item_name="Gaming Laptop",
            amount="2500.00",
            strategy_selected="delay_2_months",
            alternatives_considered=[
                {"title": "Buy Now", "description": "Immediate purchase", "tradeoffs": ["Cuts liquid buffer"]},
                {"title": "Split EMI", "description": "3-month split", "tradeoffs": ["$833/mo commitment"]},
            ],
            affected_goals=["Emergency Fund", "Japan Vacation"],
            baseline_metrics={
                "monthly_income": "6000.00",
                "current_savings": "15000.00",
                "disposable_income": "2800.00",
                "safe_to_spend_daily": "45.00",
                "emergency_runway_months": "4.2",
            },
            resulting_metrics={
                "current_savings": "12500.00",
                "safe_to_spend_daily": "35.00",
                "emergency_runway_months": "3.5",
            },
            assumptions=["Income remains stable", "No unexpected medical expenses"],
            recommendation_summary="Delay purchase by 2 months to preserve liquidity.",
            status="active",
        )

        saved = save_decision_memory(db_session, sample_user.id, data)
        assert saved.id is not None
        assert saved.item_name == "Gaming Laptop"
        assert saved.amount == "2500.00"
        assert saved.strategy_selected == "delay_2_months"

        # Retrieve by keyword
        memories = retrieve_relevant_memory(db_session, sample_user.id, query="laptop")
        assert len(memories) == 1
        assert memories[0].item_name == "Gaming Laptop"

        # Retrieve by decision type
        type_memories = retrieve_relevant_memory(db_session, sample_user.id, decision_type="large_purchase")
        assert len(type_memories) == 1

        # Retrieve non-matching query
        no_match = retrieve_relevant_memory(db_session, sample_user.id, query="sports car")
        assert len(no_match) == 0

    def test_02_memory_drift_evaluation(self, db_session, sample_user):
        data = DecisionMemoryCreateSchema(
            user_action="Buy MacBook Pro",
            decision="Delay 3 months",
            decision_type="large_purchase",
            item_name="MacBook Pro",
            amount="3000.00",
            baseline_metrics={
                "monthly_income": "4000.00",  # baseline was lower income
                "current_savings": "8000.00",
                "disposable_income": "1000.00",
                "safe_to_spend_daily": "15.00",
                "emergency_runway_months": "2.0",
            },
        )
        saved = save_decision_memory(db_session, sample_user.id, data)

        # Evaluate drift against current profile ($6000 income, $15000 savings)
        drift = evaluate_memory_drift(db_session, sample_user.id, saved)
        assert drift.has_drifted is True
        assert drift.drift_severity in ["medium", "high"]
        assert "Income increased" in drift.explanation

    def test_03_proactive_insights_generation(self, db_session, sample_user):
        # Create a past decision with drifted baseline
        data = DecisionMemoryCreateSchema(
            user_action="Car purchase",
            decision="Postponed",
            decision_type="large_purchase",
            item_name="Car",
            amount="10000.00",
            baseline_metrics={
                "monthly_income": "3500.00",
                "current_savings": "5000.00",
                "safe_to_spend_daily": "10.00",
                "emergency_runway_months": "1.5",
            },
        )
        save_decision_memory(db_session, sample_user.id, data)

        insights = generate_proactive_insights(db_session, sample_user.id)
        assert len(insights) >= 1
        assert any("Circumstances Changed" in i.title or "Emergency" in i.title for i in insights)
