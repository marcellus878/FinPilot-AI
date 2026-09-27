from datetime import datetime, timedelta
from decimal import Decimal
import unittest
import uuid

from app.main import app
from tests.test_helpers import create_test_env


class TransactionsApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "tx_test@finpilot.ai")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def test_01_create_and_get_transaction(self):
        tx_data = {
            "amount": "150.75",
            "type": "expense",
            "category": "Groceries",
            "description": "Weekly supermarket run",
            "transaction_date": datetime.now().isoformat(),
        }
        res = self.client.post("/api/v1/transactions", json=tx_data)
        self.assertEqual(res.status_code, 201)
        created = res.json()
        self.assertIn("id", created)
        self.assertEqual(created["amount"], "150.75")
        self.assertEqual(created["category"], "Groceries")
        self.assertEqual(created["type"], "expense")

        tx_id = created["id"]
        res_get = self.client.get(f"/api/v1/transactions/{tx_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["id"], tx_id)

    def test_02_update_and_delete_transaction(self):
        # Create
        tx_data = {
            "amount": "50.00",
            "type": "expense",
            "category": "Entertainment",
            "description": "Cinema ticket",
            "transaction_date": datetime.now().isoformat(),
        }
        res = self.client.post("/api/v1/transactions", json=tx_data)
        self.assertEqual(res.status_code, 201)
        tx_id = res.json()["id"]

        # Update
        update_data = {
            "amount": "65.00",
            "description": "IMAX 3D Cinema ticket",
        }
        res_update = self.client.put(f"/api/v1/transactions/{tx_id}", json=update_data)
        self.assertEqual(res_update.status_code, 200)
        updated = res_update.json()
        self.assertEqual(updated["amount"], "65.00")
        self.assertEqual(updated["description"], "IMAX 3D Cinema ticket")
        self.assertEqual(updated["category"], "Entertainment")

        # Delete
        res_del = self.client.delete(f"/api/v1/transactions/{tx_id}")
        self.assertEqual(res_del.status_code, 204)

        # Confirm 404
        res_get_after = self.client.get(f"/api/v1/transactions/{tx_id}")
        self.assertEqual(res_get_after.status_code, 404)

    def test_03_transaction_filtering(self):
        now = datetime.now()
        # Add income and distinct expenses
        self.client.post(
            "/api/v1/transactions",
            json={
                "amount": "5000.00",
                "type": "income",
                "category": "Salary",
                "description": "Monthly paycheck",
                "transaction_date": now.isoformat(),
            },
        )
        self.client.post(
            "/api/v1/transactions",
            json={
                "amount": "1200.00",
                "type": "expense",
                "category": "Housing & Rent",
                "description": "Apartment rent",
                "transaction_date": (now - timedelta(days=2)).isoformat(),
            },
        )
        self.client.post(
            "/api/v1/transactions",
            json={
                "amount": "80.00",
                "type": "expense",
                "category": "Utilities",
                "description": "Electricity bill",
                "transaction_date": (now - timedelta(days=5)).isoformat(),
            },
        )

        # Filter by type = income
        res_income = self.client.get("/api/v1/transactions?type=income")
        self.assertEqual(res_income.status_code, 200)
        income_txs = res_income.json()
        self.assertTrue(all(t["type"] == "income" for t in income_txs))

        # Filter by category = Housing
        res_cat = self.client.get("/api/v1/transactions?category=Housing")
        self.assertEqual(res_cat.status_code, 200)
        cat_txs = res_cat.json()
        self.assertTrue(len(cat_txs) >= 1)
        self.assertIn("Housing", cat_txs[0]["category"])

    def test_04_expense_summary_and_intelligence(self):
        res = self.client.get("/api/v1/expenses/summary")
        self.assertEqual(res.status_code, 200)
        summary = res.json()
        self.assertIn("total_expenses", summary)
        self.assertIn("total_income", summary)
        self.assertIn("net_savings", summary)
        self.assertIn("savings_rate", summary)
        self.assertIn("essential_spending", summary)
        self.assertIn("non_essential_spending", summary)
        self.assertIn("category_breakdown", summary)

    def test_05_category_breakdown_endpoint(self):
        res = self.client.get("/api/v1/expenses/categories")
        self.assertEqual(res.status_code, 200)
        breakdown = res.json()
        self.assertIsInstance(breakdown, list)
        self.assertTrue(len(breakdown) >= 1)
        first = breakdown[0]
        self.assertIn("category", first)
        self.assertIn("total_amount", first)
        self.assertIn("percentage_of_total", first)
        self.assertIn("is_essential", first)

    def test_06_validation_negative_or_zero_amount(self):
        res = self.client.post(
            "/api/v1/transactions",
            json={
                "amount": "-50.00",
                "type": "expense",
                "category": "Groceries",
                "transaction_date": datetime.now().isoformat(),
            },
        )
        self.assertEqual(res.status_code, 422)

        res_zero = self.client.post(
            "/api/v1/transactions",
            json={
                "amount": "0.00",
                "type": "expense",
                "category": "Groceries",
                "transaction_date": datetime.now().isoformat(),
            },
        )
        self.assertEqual(res_zero.status_code, 422)

    def test_07_validation_invalid_type(self):
        res = self.client.post(
            "/api/v1/transactions",
            json={
                "amount": "50.00",
                "type": "investment_gamble",
                "category": "Crypto",
                "transaction_date": datetime.now().isoformat(),
            },
        )
        self.assertEqual(res.status_code, 422)


if __name__ == "__main__":
    unittest.main()
