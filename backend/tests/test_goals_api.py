from decimal import Decimal
import unittest
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from tests.test_helpers import create_test_env


class GoalsApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "goals_test@finpilot.ai")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def test_01_goals_crud_and_validation(self):
        # 1. Create a goal
        goal_payload = {
            "name": "Emergency Fund",
            "target_amount": 10000.00,
            "current_amount": 2000.00,
            "target_date": "2026-12-31",
            "priority": "high",
            "category": "Emergency",
            "monthly_contribution": 500.00,
            "status": "in_progress",
        }
        res_create = self.client.post("/api/v1/goals", json=goal_payload)
        self.assertEqual(res_create.status_code, 201)
        created = res_create.json()
        self.assertEqual(created["name"], "Emergency Fund")
        self.assertEqual(float(created["target_amount"]), 10000.00)
        self.assertEqual(float(created["current_amount"]), 2000.00)
        goal_id = created["id"]

        # 2. Get single goal
        res_get = self.client.get(f"/api/v1/goals/{goal_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["id"], goal_id)

        # 3. List goals
        res_list = self.client.get("/api/v1/goals")
        self.assertEqual(res_list.status_code, 200)
        self.assertGreaterEqual(len(res_list.json()), 1)

        # 4. Update goal
        res_update = self.client.put(
            f"/api/v1/goals/{goal_id}",
            json={"current_amount": 4000.00, "priority": "medium"},
        )
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(float(res_update.json()["current_amount"]), 4000.00)
        self.assertEqual(res_update.json()["priority"], "medium")

        # 5. Delete goal
        res_del = self.client.delete(f"/api/v1/goals/{goal_id}")
        self.assertEqual(res_del.status_code, 204)

        # 6. Verify deleted
        res_after = self.client.get(f"/api/v1/goals/{goal_id}")
        self.assertEqual(res_after.status_code, 404)

    def test_02_goals_analysis_and_conflicts_endpoints(self):
        # Create 2 active goals
        g1 = {
            "name": "New Laptop",
            "target_amount": 3000.00,
            "current_amount": 500.00,
            "target_date": "2026-10-01",
            "priority": "high",
            "category": "Technology",
            "monthly_contribution": 500.00,
        }
        g2 = {
            "name": "Japan Vacation",
            "target_amount": 5000.00,
            "current_amount": 1000.00,
            "target_date": "2027-01-01",
            "priority": "low",
            "category": "Travel",
            "monthly_contribution": 400.00,
        }
        self.client.post("/api/v1/goals", json=g1)
        self.client.post("/api/v1/goals", json=g2)

        # Analysis endpoint
        res_analysis = self.client.get("/api/v1/goals/analysis")
        self.assertEqual(res_analysis.status_code, 200)
        data = res_analysis.json()
        self.assertIn("total_target_amount", data)
        self.assertIn("total_saved_amount", data)
        self.assertIn("goal_evaluations", data)
        self.assertGreaterEqual(len(data["goal_evaluations"]), 2)

        # Conflicts endpoint
        res_conflicts = self.client.get("/api/v1/goals/conflicts")
        self.assertEqual(res_conflicts.status_code, 200)
        conf_data = res_conflicts.json()
        self.assertIn("conflict_detected", conf_data)
        self.assertIn("strategies", conf_data)


if __name__ == "__main__":
    unittest.main()
