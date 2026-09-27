import unittest
import uuid
from datetime import datetime, timezone, date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.models import (
    User,
    FinancialProfile,
    Transaction,
    Budget,
    Goal,
    FinancialPlan,
    Recommendation,
    DecisionHistory,
    AgentEvent,
)


class ModelArchitectureTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)

    def setUp(self):
        self.session: Session = self.SessionLocal()

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_create_user_and_all_related_entities(self):
        # 1. Create User
        user = User(
            email="testuser@example.com",
            full_name="Test User",
            is_active=True,
        )
        self.session.add(user)
        self.session.flush()

        self.assertIsNotNone(user.id)
        self.assertEqual(user.email, "testuser@example.com")

        # 2. FinancialProfile
        profile = FinancialProfile(
            user=user,
            monthly_income=Decimal("8500.00"),
            current_savings=Decimal("25000.00"),
            monthly_debt_payment=Decimal("500.00"),
            essential_expenses=Decimal("3200.00"),
            emergency_savings=Decimal("15000.00"),
            dependents=2,
            risk_preference="moderate",
        )
        self.session.add(profile)

        # 3. Transaction
        tx = Transaction(
            user=user,
            amount=Decimal("120.50"),
            type="expense",
            category="groceries",
            description="Supermarket run",
            transaction_date=datetime.now(timezone.utc),
        )
        self.session.add(tx)

        # 4. Budget
        budget = Budget(
            user=user,
            category="groceries",
            monthly_limit=Decimal("600.00"),
            period="monthly",
        )
        self.session.add(budget)

        # 5. Goal
        goal = Goal(
            user=user,
            name="Emergency Fund",
            target_amount=Decimal("20000.00"),
            current_amount=Decimal("15000.00"),
            target_date=date(2027, 12, 31),
            priority="high",
            status="in_progress",
        )
        self.session.add(goal)

        # 6. FinancialPlan
        plan = FinancialPlan(
            user=user,
            plan_data={"strategy": "50/30/20", "allocations": {"needs": 50, "wants": 30, "savings": 20}},
            is_active=True,
        )
        self.session.add(plan)

        # 7. Recommendation
        rec = Recommendation(
            user=user,
            recommendation_type="debt_paydown",
            message="Increase monthly debt payment by $100 to reduce total interest.",
            status="active",
        )
        self.session.add(rec)

        # 8. DecisionHistory
        decision = DecisionHistory(
            user=user,
            user_action="Can I afford a $1500 laptop?",
            decision="Recommended delaying purchase by 1 month to keep emergency buffer intact.",
            financial_impact={"immediate_cash_outflow": 1500, "budget_impact": "discretionary"},
            status="accepted",
        )
        self.session.add(decision)

        # 9. AgentEvent
        event = AgentEvent(
            user=user,
            event_type="plan_rebalance_suggested",
            previous_state={"savings_rate": 0.15},
            new_state={"savings_rate": 0.20},
            responsible_agent="advisor_agent",
        )
        self.session.add(event)

        self.session.commit()

        # Reload user and check relationships
        reloaded_user = self.session.query(User).filter_by(id=user.id).one()
        self.assertIsNotNone(reloaded_user.financial_profile)
        self.assertEqual(reloaded_user.financial_profile.monthly_income, Decimal("8500.00"))
        self.assertEqual(len(reloaded_user.transactions), 1)
        self.assertEqual(reloaded_user.transactions[0].amount, Decimal("120.50"))
        self.assertEqual(len(reloaded_user.budgets), 1)
        self.assertEqual(len(reloaded_user.goals), 1)
        self.assertEqual(len(reloaded_user.financial_plans), 1)
        self.assertEqual(len(reloaded_user.recommendations), 1)
        self.assertEqual(len(reloaded_user.decision_history), 1)
        self.assertEqual(len(reloaded_user.agent_events), 1)

    def test_cascade_delete(self):
        user = User(
            email="cascade_test@example.com",
            full_name="Cascade User",
        )
        self.session.add(user)
        self.session.flush()

        tx = Transaction(
            user=user,
            amount=Decimal("50.00"),
            type="expense",
            category="dining",
            transaction_date=datetime.now(timezone.utc),
        )
        self.session.add(tx)
        self.session.commit()

        user_id = user.id
        self.session.delete(user)
        self.session.commit()

        # Verify cascade deletion
        remaining_tx = self.session.query(Transaction).filter_by(user_id=user_id).all()
        self.assertEqual(len(remaining_tx), 0)


if __name__ == "__main__":
    unittest.main()
