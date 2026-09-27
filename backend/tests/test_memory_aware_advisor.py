import unittest
import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from tests.test_helpers import create_test_env


class MemoryAwareAdvisorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "memory_test@finpilot.ai")

        # Setup base profile
        prof_payload = {
            "monthly_income": 6500.00,
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

    def test_01_create_and_list_decision_memory_api(self):
        payload = {
            "user_action": "Can I afford a $3,000 mountain bike?",
            "decision": "Verdict: AFFORDABLE_WITH_TRADE_OFFS",
            "decision_type": "large_purchase",
            "item_name": "Mountain Bike",
            "amount": "3000.00",
            "strategy_selected": "proceed_with_budget_buffer",
            "baseline_metrics": {
                "monthly_income": "6500.00",
                "current_savings": "20000.00",
            },
            "status": "active",
        }
        res = self.client.post("/api/v1/decisions/memory", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["item_name"], "Mountain Bike")
        self.assertEqual(data["strategy_selected"], "proceed_with_budget_buffer")
        decision_id = data["id"]

        # List decision memories
        list_res = self.client.get("/api/v1/decisions/memory")
        self.assertEqual(list_res.status_code, 200)
        memories = list_res.json()
        self.assertTrue(len(memories) >= 1)
        self.assertEqual(memories[0]["item_name"], "Mountain Bike")
        self.assertIn("drift_assessment", memories[0])

        # Get specific memory detail
        detail_res = self.client.get(f"/api/v1/decisions/memory/{decision_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["id"], decision_id)
        self.assertIsNotNone(detail["drift_assessment"])

    def test_02_proactive_insights_api(self):
        res = self.client.get("/api/v1/decisions/insights")
        self.assertEqual(res.status_code, 200)
        insights = res.json()
        self.assertIsInstance(insights, list)

    def test_03_memory_aware_advisor_chat_flow(self):
        # Seed a decision
        payload = {
            "user_action": "Buy $2000 TV",
            "decision": "Verdict: SUSTAINABLE",
            "decision_type": "large_purchase",
            "item_name": "OLED TV",
            "amount": "2000.00",
            "strategy_selected": "buy_now",
            "baseline_metrics": {"monthly_income": "6500.00"},
            "status": "active",
        }
        self.client.post("/api/v1/decisions/memory", json=payload)

        # Ask advisor about the TV
        chat_res = self.client.post(
            "/api/v1/advisor/chat",
            json={"message": "What did I decide previously about the OLED TV?"},
        )
        self.assertEqual(chat_res.status_code, 200)
        chat_data = chat_res.json()
        self.assertIn(chat_data["intent"], ["memory_query", "decision_evaluation", "general_financial_question"])
        self.assertTrue(len(chat_data["financial_facts"]) > 0)
        self.assertTrue(len(chat_data["execution_trace"]) > 0)


if __name__ == "__main__":
    unittest.main()
