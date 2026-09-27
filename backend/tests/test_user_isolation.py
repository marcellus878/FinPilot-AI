import unittest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


class UserIsolationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        # Register User A
        res_a = cls.client.post("/api/v1/auth/register", json={
            "email": "user_a@example.com",
            "password": "PasswordA123!",
            "name": "User Alpha",
        })
        cls.token_a = res_a.json()["access_token"]
        cls.user_a_id = res_a.json()["user"]["id"]
        cls.headers_a = {"Authorization": f"Bearer {cls.token_a}"}

        # Register User B
        res_b = cls.client.post("/api/v1/auth/register", json={
            "email": "user_b@example.com",
            "password": "PasswordB123!",
            "name": "User Beta",
        })
        cls.token_b = res_b.json()["access_token"]
        cls.user_b_id = res_b.json()["user"]["id"]
        cls.headers_b = {"Authorization": f"Bearer {cls.token_b}"}

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=cls.engine)

    def test_01_profile_isolation(self):
        # User A sets up profile
        res = self.client.post("/api/v1/profile", headers=self.headers_a, json={
            "monthly_income": "8000.00",
            "current_savings": "25000.00",
            "monthly_debt_payment": "500.00",
            "essential_expenses": "3000.00",
            "dependents": 2,
            "risk_preference": "aggressive",
        })
        self.assertEqual(res.status_code, 201)

        # User B gets own profile -> defaults to 0
        res_b = self.client.get("/api/v1/profile", headers=self.headers_b)
        self.assertEqual(res_b.status_code, 200)
        self.assertEqual(res_b.json()["monthly_income"], "0.00")

        # User B attempts to access User A's profile via direct user_id endpoint -> 403 Forbidden
        res_cross = self.client.get(f"/api/v1/profile/{self.user_a_id}", headers=self.headers_b)
        self.assertEqual(res_cross.status_code, 403)

    def test_02_transaction_isolation(self):
        # User A creates a transaction
        res_tx = self.client.post("/api/v1/transactions", headers=self.headers_a, json={
            "amount": "150.00",
            "type": "expense",
            "category": "Groceries",
            "description": "Weekly grocery haul",
            "transaction_date": "2026-09-27T12:00:00Z",
        })
        self.assertEqual(res_tx.status_code, 201)
        tx_a_id = res_tx.json()["id"]

        # User B lists transactions -> should be empty
        res_b_list = self.client.get("/api/v1/transactions", headers=self.headers_b)
        self.assertEqual(res_b_list.status_code, 200)
        self.assertEqual(len(res_b_list.json()), 0)

        # User B attempts to get User A's transaction by ID -> 404
        res_b_get = self.client.get(f"/api/v1/transactions/{tx_a_id}", headers=self.headers_b)
        self.assertEqual(res_b_get.status_code, 404)

        # User B attempts to update User A's transaction -> 404
        res_b_put = self.client.put(f"/api/v1/transactions/{tx_a_id}", headers=self.headers_b, json={
            "amount": "999.00",
        })
        self.assertEqual(res_b_put.status_code, 404)

        # User B attempts to delete User A's transaction -> 404
        res_b_del = self.client.delete(f"/api/v1/transactions/{tx_a_id}", headers=self.headers_b)
        self.assertEqual(res_b_del.status_code, 404)

    def test_03_budget_isolation(self):
        # User A creates a budget
        res_bgt = self.client.post("/api/v1/budgets", headers=self.headers_a, json={
            "category": "Dining Out",
            "monthly_limit": "400.00",
            "period": "monthly",
        })
        self.assertEqual(res_bgt.status_code, 201)
        bgt_a_id = res_bgt.json()["id"]

        # User B lists budgets -> empty
        res_b_list = self.client.get("/api/v1/budgets", headers=self.headers_b)
        self.assertEqual(res_b_list.status_code, 200)
        self.assertEqual(len(res_b_list.json()), 0)

        # User B attempts to access User A's budget -> 404
        res_b_get = self.client.get(f"/api/v1/budgets/{bgt_a_id}", headers=self.headers_b)
        self.assertEqual(res_b_get.status_code, 404)

    def test_04_goal_isolation(self):
        # User A creates a goal
        res_goal = self.client.post("/api/v1/goals", headers=self.headers_a, json={
            "name": "Alpha Emergency Fund",
            "target_amount": "10000.00",
            "current_amount": "2000.00",
            "priority": "high",
            "category": "emergency",
        })
        self.assertEqual(res_goal.status_code, 201)
        goal_a_id = res_goal.json()["id"]

        # User B lists goals -> empty
        res_b_list = self.client.get("/api/v1/goals", headers=self.headers_b)
        self.assertEqual(res_b_list.status_code, 200)
        self.assertEqual(len(res_b_list.json()), 0)

        # User B attempts to get User A's goal -> 404
        res_b_get = self.client.get(f"/api/v1/goals/{goal_a_id}", headers=self.headers_b)
        self.assertEqual(res_b_get.status_code, 404)

    def test_05_decision_memory_isolation(self):
        # User A creates a decision memory
        res_dec = self.client.post("/api/v1/decisions/memory", headers=self.headers_a, json={
            "decision_type": "purchase",
            "item_name": "MacBook Pro M3",
            "amount": "2499.00",
            "user_action": "Simulate MacBook purchase",
            "decision": "Recommended purchase after 2 months buffer",
        })
        self.assertEqual(res_dec.status_code, 201)
        dec_a_id = res_dec.json()["id"]

        # User B lists decision memory -> empty
        res_b_list = self.client.get("/api/v1/decisions/memory", headers=self.headers_b)
        self.assertEqual(res_b_list.status_code, 200)
        self.assertEqual(len(res_b_list.json()), 0)

        # User B attempts to access User A's decision memory -> 404
        res_b_get = self.client.get(f"/api/v1/decisions/memory/{dec_a_id}", headers=self.headers_b)
        self.assertEqual(res_b_get.status_code, 404)
