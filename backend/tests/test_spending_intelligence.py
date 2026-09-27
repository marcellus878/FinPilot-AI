from datetime import datetime, timedelta
from decimal import Decimal
import unittest
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.financial_engine.categorization import (
    categorize_transaction,
    classify_essentiality,
)
from app.financial_engine.spending_intelligence import (
    analyze_spending_patterns,
    calculate_spending_intelligence,
    detect_hidden_expenses,
    detect_miscellaneous_spending,
    detect_recurring_expenses,
    detect_spending_habits,
)
from app.main import app
from app.models.transaction import Transaction
from tests.test_helpers import create_test_env


class DummyTx:
    def __init__(self, amount, tx_type, category, description, transaction_date):
        self.amount = Decimal(str(amount))
        self.type = tx_type
        self.category = category
        self.description = description
        self.transaction_date = transaction_date


class SpendingIntelligenceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "spending_test@finpilot.ai")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def test_01_categorization_and_essentiality(self):
        cat1 = categorize_transaction("Swiggy Bangalore delivery", "expense")
        self.assertEqual(cat1.category, "Food")
        ess1 = classify_essentiality(cat1.category, "Swiggy Bangalore delivery", "expense")
        self.assertEqual(ess1.essentiality, "discretionary")

        cat2 = categorize_transaction("Monthly Apartment Rent to Landlord", "expense")
        self.assertEqual(cat2.category, "Rent/Housing")
        ess2 = classify_essentiality(cat2.category, "Rent", "expense")
        self.assertEqual(ess2.essentiality, "essential")

        cat3 = categorize_transaction("Apollo Pharmacy Medicine", "expense")
        self.assertEqual(cat3.category, "Healthcare")
        ess3 = classify_essentiality(cat3.category, "Apollo Pharmacy Medicine", "expense")
        self.assertEqual(ess3.essentiality, "essential")

    def test_02_spending_patterns(self):
        # Create weekend heavy spending (Saturday/Sunday)
        saturday = datetime(2026, 3, 21)  # Saturday
        sunday = datetime(2026, 3, 22)    # Sunday
        tuesday = datetime(2026, 3, 17)   # Tuesday

        txs = [
            DummyTx(300, "expense", "Food", "Swiggy weekend feast", saturday),
            DummyTx(250, "expense", "Entertainment", "Movie tickets", sunday),
            DummyTx(100, "expense", "Groceries", "Weekly veggies", tuesday),
        ]

        patterns = analyze_spending_patterns(txs)
        self.assertTrue(any(p.pattern_type == "weekend_concentration" for p in patterns))
        self.assertTrue(any(p.pattern_type == "category_concentration" for p in patterns))

    def test_03_spending_habits(self):
        now = datetime.now()
        txs = [
            DummyTx(40, "expense", "Food", "Swiggy order 1", now - timedelta(days=1)),
            DummyTx(45, "expense", "Food", "Swiggy order 2", now - timedelta(days=3)),
            DummyTx(50, "expense", "Food", "Swiggy order 3", now - timedelta(days=5)),
            DummyTx(55, "expense", "Food", "Swiggy order 4", now - timedelta(days=8)),
            DummyTx(30, "expense", "Food", "Starbucks latte", now - timedelta(days=2)),
            DummyTx(32, "expense", "Food", "Starbucks coffee", now - timedelta(days=4)),
            DummyTx(35, "expense", "Food", "Starbucks frappuccino", now - timedelta(days=6)),
        ]

        habits = detect_spending_habits(txs)
        habit_names = [h.habit_name for h in habits]
        self.assertIn("Frequent On-Demand Food Delivery", habit_names)
        self.assertIn("Regular Coffee & Cafe Visits", habit_names)

    def test_04_recurring_and_hidden_expenses(self):
        d1 = datetime(2026, 1, 5)
        d2 = datetime(2026, 2, 5)
        d3 = datetime(2026, 3, 5)

        txs = [
            DummyTx(15.99, "expense", "Entertainment", "Netflix Premium", d1),
            DummyTx(15.99, "expense", "Entertainment", "Netflix Premium", d2),
            DummyTx(15.99, "expense", "Entertainment", "Netflix Premium", d3),
            DummyTx(1200, "expense", "Rent/Housing", "Apartment Rent", d1),
            DummyTx(1200, "expense", "Rent/Housing", "Apartment Rent", d2),
            DummyTx(1200, "expense", "Rent/Housing", "Apartment Rent", d3),
        ]

        recurring = detect_recurring_expenses(txs)
        self.assertEqual(len(recurring), 2)
        netflix = next(r for r in recurring if "Netflix" in r.merchant)
        self.assertEqual(netflix.frequency, "monthly")
        self.assertEqual(netflix.occurrence_count, 3)

        # Hidden expense detector checks recurring items <= $35
        hidden = detect_hidden_expenses(txs, recurring)
        self.assertEqual(len(hidden), 1)
        self.assertEqual(hidden[0].merchant, "Netflix")
        self.assertGreater(hidden[0].annualized_cost, Decimal("180.00"))

    def test_05_miscellaneous_spending_detector(self):
        txs = [
            DummyTx(50, "expense", "Miscellaneous", "Random shop 1", datetime.now()),
            DummyTx(75, "expense", "Miscellaneous", "Unknown charge 2", datetime.now()),
            DummyTx(100, "expense", "Food", "Dinner", datetime.now()),
        ]
        misc = detect_miscellaneous_spending(txs)
        self.assertEqual(misc.total_miscellaneous_amount, Decimal("125.00"))
        self.assertEqual(misc.transaction_count, 2)
        self.assertGreater(misc.percentage_of_expenses, Decimal("50.00"))
        self.assertEqual(misc.leak_severity, "high")

    def test_06_spending_intelligence_api_endpoint(self):
        # Add test transactions via API
        self.client.post(
            "/api/v1/transactions",
            json={
                "amount": "14.99",
                "type": "expense",
                "category": "Entertainment",
                "description": "Spotify Subscription",
                "transaction_date": (datetime.now() - timedelta(days=30)).isoformat(),
            },
        )
        self.client.post(
            "/api/v1/transactions",
            json={
                "amount": "14.99",
                "type": "expense",
                "category": "Entertainment",
                "description": "Spotify Subscription",
                "transaction_date": datetime.now().isoformat(),
            },
        )

        res = self.client.get("/api/v1/transactions/intelligence")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("essential_percentage", data)
        self.assertIn("discretionary_percentage", data)
        self.assertIn("patterns", data)
        self.assertIn("recurring_expenses", data)
        self.assertIn("hidden_expenses", data)
        self.assertIn("miscellaneous_analysis", data)


if __name__ == "__main__":
    unittest.main()
