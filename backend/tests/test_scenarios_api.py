from decimal import Decimal
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from tests.test_helpers import create_test_env


class ScenariosApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "scenarios_test@finpilot.ai")

        # Create a baseline profile
        prof_payload = {
            "monthly_income": 6000.00,
            "current_savings": 20000.00,
            "monthly_debt_payment": 500.00,
            "essential_expenses": 3000.00,
            "dependents": 1,
            "emergency_savings": 15000.00,
            "risk_preference": "moderate",
        }
        cls.client.post("/api/v1/profile", json=prof_payload)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def test_01_simulate_single_purchase_scenario(self):
        # Initial profile check
        prof_before = self.client.get("/api/v1/profile").json()

        payload = {
            "scenario_type": "one_time_purchase",
            "amount": 3500.00,
            "name": "New Gaming PC",
            "timing_months": 0,
            "description": "Custom desktop setup",
        }
        res = self.client.post("/api/v1/scenarios/simulate", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["scenario_name"], "New Gaming PC")
        self.assertEqual(float(data["before_state"]["current_savings"]), 20000.00)
        self.assertEqual(float(data["after_state"]["current_savings"]), 16500.00)
        self.assertEqual(float(data["delta"]["savings_delta"]), -3500.00)
        self.assertIn("affordability_verdict", data)

        # Crucial check: Profile in DB remains untouched
        prof_after = self.client.get("/api/v1/profile").json()
        self.assertEqual(prof_before["current_savings"], prof_after["current_savings"])

    def test_02_simulate_recurring_expense_and_income_change(self):
        # 1. New recurring expense
        res_rec = self.client.post(
            "/api/v1/scenarios/simulate",
            json={
                "scenario_type": "new_recurring_expense",
                "amount": 250.00,
                "name": "Health Club Membership",
            },
        )
        self.assertEqual(res_rec.status_code, 200)
        self.assertEqual(float(res_rec.json()["delta"]["monthly_essential_expenses_delta"]), 250.00)

        # 2. Income change
        res_inc = self.client.post(
            "/api/v1/scenarios/simulate",
            json={
                "scenario_type": "income_change",
                "amount": 1000.00,
                "name": "Annual Bonus / Raise",
            },
        )
        self.assertEqual(res_inc.status_code, 200)
        self.assertEqual(float(res_inc.json()["delta"]["monthly_income_delta"]), 1000.00)

    def test_03_compare_three_scenarios(self):
        payload = {
            "scenarios": [
                {
                    "id": "opt_a",
                    "name": "Buy Laptop Now",
                    "type": "one_time_purchase",
                    "amount": 2000.00,
                    "timing_months": 0,
                },
                {
                    "id": "opt_b",
                    "name": "Buy Budget Model",
                    "type": "one_time_purchase",
                    "amount": 1200.00,
                    "timing_months": 0,
                },
                {
                    "id": "opt_c",
                    "name": "Buy Laptop in 3 Months",
                    "type": "one_time_purchase",
                    "amount": 2000.00,
                    "timing_months": 3,
                },
            ]
        }
        res = self.client.post("/api/v1/scenarios/compare", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("baseline", data)
        self.assertEqual(len(data["scenarios"]), 3)
        self.assertEqual(len(data["tradeoff_summary"]), 3)


if __name__ == "__main__":
    unittest.main()
