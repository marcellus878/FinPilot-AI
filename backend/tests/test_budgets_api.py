from decimal import Decimal
import unittest
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from tests.test_helpers import create_test_env


class BudgetsApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "budget_test@finpilot.ai")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def test_01_create_and_get_budget(self):
        budget_payload = {
            "category": "Groceries",
            "monthly_limit": "500.00",
            "period": "monthly",
        }
        res = self.client.post("/api/v1/budgets", json=budget_payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("id", data)
        self.assertEqual(data["category"], "Groceries")
        self.assertEqual(data["monthly_limit"], "500.00")

        budget_id = data["id"]
        res_get = self.client.get(f"/api/v1/budgets/{budget_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["id"], budget_id)

    def test_02_upsert_budget(self):
        # Setting budget for same category updates the existing one
        budget_payload = {
            "category": "Groceries",
            "monthly_limit": "650.00",
            "period": "monthly",
        }
        res = self.client.post("/api/v1/budgets", json=budget_payload)
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["monthly_limit"], "650.00")

        # List budgets and confirm only one Groceries entry exists
        res_list = self.client.get("/api/v1/budgets")
        self.assertEqual(res_list.status_code, 200)
        groceries = [b for b in res_list.json() if b["category"].lower() == "groceries"]
        self.assertEqual(len(groceries), 1)
        self.assertEqual(groceries[0]["monthly_limit"], "650.00")

    def test_03_update_and_delete_budget(self):
        # Create Dining budget
        res = self.client.post(
            "/api/v1/budgets",
            json={"category": "Dining Out", "monthly_limit": "200.00", "period": "monthly"},
        )
        b_id = res.json()["id"]

        # Update limit
        update_res = self.client.put(
            f"/api/v1/budgets/{b_id}",
            json={"monthly_limit": "250.00"},
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertEqual(update_res.json()["monthly_limit"], "250.00")

        # Delete
        del_res = self.client.delete(f"/api/v1/budgets/{b_id}")
        self.assertEqual(del_res.status_code, 204)

        # Get deleted returns 404
        get_res = self.client.get(f"/api/v1/budgets/{b_id}")
        self.assertEqual(get_res.status_code, 404)

    def test_04_budget_performance(self):
        # Seed budget & transaction to test performance calculations
        self.client.post(
            "/api/v1/budgets",
            json={"category": "Entertainment", "monthly_limit": "300.00", "period": "monthly"},
        )
        from datetime import datetime
        self.client.post(
            "/api/v1/transactions",
            json={
                "amount": "120.00",
                "type": "expense",
                "category": "Entertainment",
                "description": "Cinema and concert",
                "transaction_date": datetime.now().isoformat(),
            },
        )

        res = self.client.get("/api/v1/budgets/performance")
        self.assertEqual(res.status_code, 200)
        perf = res.json()
        self.assertIn("total_budgeted", perf)
        self.assertIn("total_spent", perf)
        self.assertIn("total_remaining", perf)
        self.assertIn("category_statuses", perf)
        self.assertTrue(len(perf["category_statuses"]) > 0)

        ent_status = next(
            (c for c in perf["category_statuses"] if c["category"] == "Entertainment"),
            None,
        )
        self.assertIsNotNone(ent_status)
        self.assertEqual(ent_status["monthly_limit"], "300.00")
        self.assertEqual(ent_status["actual_spent"], "120.00")
        self.assertEqual(ent_status["remaining_amount"], "180.00")
        self.assertEqual(ent_status["percentage_consumed"], "40.00")
        self.assertFalse(ent_status["is_over_budget"])

    def test_05_validation_negative_monthly_limit(self):
        res = self.client.post(
            "/api/v1/budgets",
            json={"category": "Books", "monthly_limit": "-50.00"},
        )
        self.assertEqual(res.status_code, 422)


if __name__ == "__main__":
    unittest.main()
