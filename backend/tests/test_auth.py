import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models.user import User


class AuthApiTestCase(unittest.TestCase):
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

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=cls.engine)

    def test_01_register_success(self):
        payload = {
            "email": "testuser@example.com",
            "password": "Password123!",
            "name": "Test User",
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["user"]["email"], "testuser@example.com")
        self.assertEqual(data["user"]["full_name"], "Test User")
        self.assertFalse(data["user"]["has_profile"])

    def test_02_register_duplicate_email(self):
        payload = {
            "email": "testuser@example.com",
            "password": "AnotherPassword123!",
            "name": "Duplicate User",
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn("already exists", res.json()["detail"])

    def test_03_register_weak_password(self):
        payload = {
            "email": "weak@example.com",
            "password": "short",
            "name": "Weak Pass",
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        # Validation error (min_length=8)
        self.assertIn(res.status_code, (400, 422))

    def test_04_register_invalid_email(self):
        payload = {
            "email": "not-an-email",
            "password": "ValidPassword123!",
            "name": "Bad Email",
        }
        res = self.client.post("/api/v1/auth/register", json=payload)
        self.assertEqual(res.status_code, 422)

    def test_05_login_success(self):
        payload = {
            "email": "testuser@example.com",
            "password": "Password123!",
        }
        res = self.client.post("/api/v1/auth/login", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["email"], "testuser@example.com")

    def test_06_login_invalid_password(self):
        payload = {
            "email": "testuser@example.com",
            "password": "WrongPassword123!",
        }
        res = self.client.post("/api/v1/auth/login", json=payload)
        self.assertEqual(res.status_code, 401)

    def test_07_login_nonexistent_email(self):
        payload = {
            "email": "ghost@example.com",
            "password": "Password123!",
        }
        res = self.client.post("/api/v1/auth/login", json=payload)
        self.assertEqual(res.status_code, 401)

    def test_08_get_me_authenticated(self):
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "testuser@example.com",
            "password": "Password123!",
        })
        token = login_res.json()["access_token"]

        res = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["email"], "testuser@example.com")
        self.assertEqual(data["full_name"], "Test User")

    def test_09_get_me_unauthorized(self):
        res = self.client.get("/api/v1/auth/me")
        self.assertEqual(res.status_code, 401)

    def test_10_get_me_invalid_token(self):
        res = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        self.assertEqual(res.status_code, 401)

    def test_11_update_me(self):
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": "testuser@example.com",
            "password": "Password123!",
        })
        token = login_res.json()["access_token"]

        # Update full name
        res = self.client.put(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"full_name": "Updated Name"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["full_name"], "Updated Name")
