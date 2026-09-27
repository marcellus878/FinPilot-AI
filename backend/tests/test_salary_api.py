from datetime import datetime, timedelta
from decimal import Decimal
import unittest
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from tests.test_helpers import create_test_env


class SalaryApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "salary_test@finpilot.ai")

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def test_01_salary_profile_get_and_update(self):
        res = self.client.get("/api/v1/salary/profile")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("monthly_income", data)
        self.assertIn("days_remaining", data)

        # Update profile
        payload = {
            "monthly_income": "60000.00",
            "expected_salary_day": 1,
            "additional_recurring_income": "5000.00",
            "savings_target": "15000.00",
            "essential_spending_allowance": "15000.00",
            "discretionary_allowance": "10000.00",
        }
        res_update = self.client.put("/api/v1/salary/profile", json=payload)
        self.assertEqual(res_update.status_code, 200)
        up_data = res_update.json()
        self.assertEqual(up_data["monthly_income"], "60000.00")
        self.assertEqual(up_data["total_monthly_income"], "65000.00")

    def test_02_recurring_commitments_crud(self):
        comm_payload = {
            "name": "Apartment Rent",
            "category": "Rent/Housing",
            "amount": "18000.00",
            "frequency": "monthly",
            "next_expected_date": datetime.now().isoformat(),
            "description": "Monthly flat rent",
            "is_active": True,
            "is_confirmed": True,
        }
        res = self.client.post("/api/v1/salary/recurring-expenses", json=comm_payload)
        self.assertEqual(res.status_code, 201)
        created = res.json()
        self.assertIn("id", created)
        self.assertEqual(created["name"], "Apartment Rent")
        comm_id = created["id"]

        # List
        res_list = self.client.get("/api/v1/salary/recurring-expenses")
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(any(c["id"] == comm_id for c in res_list.json()))

        # Update
        res_edit = self.client.put(
            f"/api/v1/salary/recurring-expenses/{comm_id}",
            json={"amount": "19000.00"},
        )
        self.assertEqual(res_edit.status_code, 200)
        self.assertEqual(res_edit.json()["amount"], "19000.00")

        # Delete
        res_del = self.client.delete(f"/api/v1/salary/recurring-expenses/{comm_id}")
        self.assertEqual(res_del.status_code, 204)

    def test_03_salary_allocation_and_custom_calculate(self):
        # First set recurring commitments and salary
        self.client.put(
            "/api/v1/salary/profile",
            json={
                "monthly_income": "60000.00",
                "additional_recurring_income": "0.00",
                "savings_target": "15000.00",
                "essential_spending_allowance": "12000.00",
                "discretionary_allowance": "8000.00",
            },
        )
        self.client.post(
            "/api/v1/salary/recurring-expenses",
            json={
                "name": "EMI / Rent",
                "category": "Rent/Housing",
                "amount": "20000.00",
                "frequency": "monthly",
            },
        )

        res_alloc = self.client.get("/api/v1/salary/allocation")
        self.assertEqual(res_alloc.status_code, 200)
        alloc = res_alloc.json()
        self.assertTrue(alloc["is_feasible"])
        self.assertEqual(alloc["fixed_commitments"], "20000.00")
        self.assertEqual(alloc["remaining_buffer"], "5000.00")

        # Custom calculate preview (infeasible scenario)
        calc_req = {
            "monthly_income": "50000.00",
            "fixed_commitments": "25000.00",
            "essential_allowance": "15000.00",
            "savings_target": "15000.00",
            "discretionary_allowance": "0.00",
        }
        res_calc = self.client.post("/api/v1/salary/allocation/calculate", json=calc_req)
        self.assertEqual(res_calc.status_code, 200)
        calc_data = res_calc.json()
        self.assertFalse(calc_data["is_feasible"])
        self.assertEqual(calc_data["deficit_amount"], "5000.00")
        self.assertEqual(len(calc_data["alternatives"]), 3)

    def test_04_safe_to_spend_endpoint(self):
        res = self.client.get("/api/v1/salary/safe-to-spend")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("safe_to_spend_amount", data)
        self.assertIn("daily_safe_to_spend", data)
        self.assertIn("days_remaining", data)

    def test_05_survival_projection_endpoint(self):
        res = self.client.get("/api/v1/salary/survival-projection")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("status", data)
        self.assertIn("projected_end_of_month_balance", data)
        self.assertIn("daily_spending_capacity", data)

    def test_06_monthly_plan_recalculate(self):
        res = self.client.post("/api/v1/salary/monthly-plan/recalculate")
        self.assertEqual(res.status_code, 200)
        plan = res.json()
        self.assertIn("salary_profile", plan)
        self.assertIn("allocation", plan)
        self.assertIn("safe_to_spend", plan)
        self.assertIn("survival_projection", plan)


if __name__ == "__main__":
    unittest.main()
