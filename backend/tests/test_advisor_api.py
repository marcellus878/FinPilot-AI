import unittest

from app.main import app
from tests.test_helpers import create_test_env


class AdvisorApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "advisor_test@finpilot.ai")

        # Setup base profile
        prof_payload = {
            "monthly_income": 7000.00,
            "current_savings": 25000.00,
            "monthly_debt_payment": 600.00,
            "essential_expenses": 3200.00,
            "dependents": 2,
            "emergency_savings": 20000.00,
            "risk_preference": "moderate",
        }
        cls.client.post("/api/v1/profile", json=prof_payload)

        # Add sample transaction
        cls.client.post(
            "/api/v1/transactions",
            json={
                "amount": 140.00,
                "type": "expense",
                "category": "Food & Dining",
                "description": "Weekly grocery run",
                "transaction_date": "2026-09-27T10:00:00",
            },
        )

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def test_01_advisor_chat_spending_analysis(self):
        payload = {
            "message": "Analyze my spending habits and tell me how my discretionary expenses look.",
        }
        response = self.client.post("/api/v1/advisor/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertIn("intent", data)
        self.assertEqual(data["intent"], "spending_analysis")
        self.assertIn("financial_facts", data)
        self.assertIn("execution_trace", data)
        self.assertIn("recommendations", data)

    def test_02_advisor_chat_expense_reduction(self):
        payload = {
            "message": "Where can I reduce expenses and save more money this month?",
        }
        response = self.client.post("/api/v1/advisor/chat", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intent"], "expense_reduction")
        self.assertIn("recommendations", data)

    def test_03_get_recommendations(self):
        response = self.client.get("/api/v1/advisor/recommendations")
        self.assertEqual(response.status_code, 200)
        recs = response.json()
        self.assertIsInstance(recs, list)


if __name__ == "__main__":
    unittest.main()
