import unittest
import uuid
from decimal import Decimal

from app.main import app
from tests.test_helpers import create_test_env


class FinancialProfileApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "profile_test@finpilot.ai")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def test_01_get_initial_profile_for_first_time_user(self):
        response = self.client.get("/api/v1/profile")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("id", data)
        self.assertIn("user_id", data)
        self.assertEqual(data["monthly_income"], "0.00")
        self.assertEqual(data["risk_preference"], "moderate")
        self.assertIn("indicators", data)
        self.assertEqual(data["indicators"]["disposable_income"], "0.00")
        self.assertEqual(data["indicators"]["savings_rate"], "0.00")

    def test_02_create_or_set_profile(self):
        payload = {
            "monthly_income": "6000.00",
            "current_savings": "18000.00",
            "monthly_debt_payment": "600.00",
            "essential_expenses": "3000.00",
            "dependents": 1,
            "risk_preference": "moderate",
        }
        response = self.client.post("/api/v1/profile", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["monthly_income"], "6000.00")
        self.assertEqual(data["current_savings"], "18000.00")
        self.assertEqual(data["monthly_debt_payment"], "600.00")
        self.assertEqual(data["essential_expenses"], "3000.00")
        self.assertEqual(data["dependents"], 1)
        self.assertEqual(data["risk_preference"], "moderate")

        # Verify computed indicators
        # Disposable income: 6000 - 3000 - 600 = 2400.00
        self.assertEqual(data["indicators"]["disposable_income"], "2400.00")
        # Savings rate: (2400 / 6000) * 100 = 40.00%
        self.assertEqual(data["indicators"]["savings_rate"], "40.00")
        # Expense ratio: (3000 / 6000) * 100 = 50.00%
        self.assertEqual(data["indicators"]["expense_ratio"], "50.00")
        # DTI: (600 / 6000) * 100 = 10.00%
        self.assertEqual(data["indicators"]["debt_to_income_ratio"], "10.00")
        # Emergency fund target: 3000 * 6 = 18000.00 (current 18000.00 -> 6.0 months, funded)
        self.assertEqual(data["indicators"]["emergency_fund"]["target_amount"], "18000.00")
        self.assertEqual(data["indicators"]["emergency_fund"]["months_covered"], "6.00")
        self.assertEqual(data["indicators"]["emergency_fund"]["status_label"], "optimal")

    def test_03_retrieve_saved_profile(self):
        response = self.client.get("/api/v1/profile")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["monthly_income"], "6000.00")
        self.assertEqual(data["indicators"]["disposable_income"], "2400.00")

    def test_04_update_profile(self):
        update_payload = {
            "monthly_income": "8000.00",
            "risk_preference": "aggressive",
        }
        response = self.client.put("/api/v1/profile", json=update_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["monthly_income"], "8000.00")
        self.assertEqual(data["risk_preference"], "aggressive")
        self.assertEqual(data["essential_expenses"], "3000.00")  # preserved

        # New disposable: 8000 - 3000 - 600 = 4400.00
        self.assertEqual(data["indicators"]["disposable_income"], "4400.00")

    def test_05_validation_negative_values(self):
        bad_payload = {
            "monthly_income": "-500.00",
        }
        response = self.client.put("/api/v1/profile", json=bad_payload)
        self.assertEqual(response.status_code, 422)

    def test_06_validation_invalid_risk_preference(self):
        bad_payload = {
            "risk_preference": "super_speculative",
        }
        response = self.client.put("/api/v1/profile", json=bad_payload)
        self.assertEqual(response.status_code, 422)

    def test_07_nonexistent_user_lookup(self):
        fake_uuid = str(uuid.uuid4())
        response = self.client.get(f"/api/v1/profile/{fake_uuid}")
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
