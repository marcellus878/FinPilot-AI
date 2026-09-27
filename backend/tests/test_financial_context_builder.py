from datetime import date, datetime
from decimal import Decimal
import unittest
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agent.context_builder import build_financial_context
from app.core.database import Base
from app.models.budget import Budget
from app.models.financial_profile import FinancialProfile
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.models.user import User


class FinancialContextBuilderTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        self.user_id = uuid.uuid4()
        user = User(id=self.user_id, email=f"builder_{self.user_id}@example.com", full_name="Advisor Test User")
        self.db.add(user)
        
        profile = FinancialProfile(
            user_id=self.user_id,
            monthly_income=Decimal("5000.00"),
            current_savings=Decimal("15000.00"),
            monthly_debt_payment=Decimal("400.00"),
            essential_expenses=Decimal("2500.00"),
            emergency_savings=Decimal("12000.00"),
            dependents=0,
            risk_preference="moderate",
        )
        self.db.add(profile)

        # Add some transactions
        t1 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            amount=Decimal("120.00"),
            type="expense",
            category="Food & Dining",
            description="Supermarket groceries",
            transaction_date=datetime.now(),
        )
        t2 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            amount=Decimal("75.00"),
            type="expense",
            category="Entertainment",
            description="Online streaming subscription",
            transaction_date=datetime.now(),
        )
        t3 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            amount=Decimal("45.00"),
            type="expense",
            category="Other",
            description="Miscellaneous convenience purchase",
            transaction_date=datetime.now(),
        )
        self.db.add_all([t1, t2, t3])

        # Add budget
        b1 = Budget(
            id=uuid.uuid4(),
            user_id=self.user_id,
            category="Food & Dining",
            monthly_limit=Decimal("500.00"),
            period="monthly",
        )
        self.db.add(b1)

        # Add goal
        g1 = Goal(
            id=uuid.uuid4(),
            user_id=self.user_id,
            name="Emergency Buffer",
            target_amount=Decimal("20000.00"),
            current_amount=Decimal("12000.00"),
            target_date=date.today().replace(year=date.today().year + 1),
            priority="high",
            monthly_contribution=Decimal("500.00"),
            status="in_progress",
        )
        self.db.add(g1)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_build_financial_context_structure(self):
        ctx = build_financial_context(self.db, self.user_id)
        
        self.assertIn("user", ctx)
        self.assertIn("profile", ctx)
        self.assertIn("core_metrics", ctx)
        self.assertIn("expense_summary", ctx)
        self.assertIn("category_spending", ctx)
        self.assertIn("spending_intelligence", ctx)
        self.assertIn("budget_performance", ctx)
        self.assertIn("cash_flow", ctx)
        self.assertIn("goals_portfolio", ctx)
        self.assertIn("financial_health_score", ctx)

        # Verify values
        self.assertEqual(ctx["profile"]["monthly_income"], 5000.0)
        self.assertEqual(ctx["core_metrics"]["disposable_income"], 2100.0) # 5000 - 2500 - 400
        self.assertEqual(ctx["expense_summary"]["total_expenses"], 240.0) # 120 + 75 + 45
        self.assertEqual(ctx["goals_portfolio"]["active_goals_count"], 1)
        self.assertGreater(ctx["financial_health_score"]["overall_score"], 0)


if __name__ == "__main__":
    unittest.main()
