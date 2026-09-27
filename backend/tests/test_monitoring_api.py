from datetime import datetime
from decimal import Decimal
import unittest
import uuid

from app.core.security import get_current_user
from app.main import app
from app.models.financial_profile import FinancialProfile
from app.models.transaction import Transaction
from app.models.user import User
from tests.test_helpers import create_test_env


class MonitoringApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.Session, cls.test_user, cls.client = create_test_env(app, "monitoring_test@finpilot.ai")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def setUp(self):
        self.db = self.Session()
        self.user_id = self.test_user.id

        profile = self.db.query(FinancialProfile).filter(FinancialProfile.user_id == self.user_id).first()
        if not profile:
            profile = FinancialProfile(
                user_id=self.user_id,
                monthly_income=Decimal("6000.00"),
                current_savings=Decimal("15000.00"),
                monthly_debt_payment=Decimal("300.00"),
                essential_expenses=Decimal("2500.00"),
                emergency_savings=Decimal("15000.00"),
                dependents=1,
                risk_preference="moderate",
            )
            self.db.add(profile)
        else:
            profile.monthly_income = Decimal("6000.00")
            profile.current_savings = Decimal("15000.00")
            profile.essential_expenses = Decimal("2500.00")

        # Add transactions
        t1 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            amount=Decimal("300.00"),
            type="expense",
            category="Food & Dining",
            description="Restaurants",
            transaction_date=datetime.now(),
        )
        self.db.add(t1)
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_01_get_monitoring_status(self):
        resp = self.client.get("/api/v1/monitoring/status")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["has_baseline"])
        self.assertIn("plan_status", data)
        self.assertIn("summary_message", data)

    def test_02_post_monitoring_run(self):
        resp = self.client.post("/api/v1/monitoring/run")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("baseline_snapshot", data)
        self.assertIn("current_snapshot", data)
        self.assertIn("changes", data)
        self.assertIn("assessment", data)
        self.assertIn("plan_status", data)
        self.assertEqual(data["current_snapshot"]["monthly_income"], "6000.00")

    def test_03_get_monitoring_changes(self):
        resp = self.client.get("/api/v1/monitoring/changes")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)

    def test_04_get_monitoring_replanning(self):
        resp = self.client.get("/api/v1/monitoring/replanning")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        if data:
            self.assertIn("items", data)
            self.assertIn("summary", data)


if __name__ == "__main__":
    unittest.main()
