import unittest
from fastapi.testclient import TestClient
from app.main import app

class HealthEndpointTestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("FinPilot AI", data["message"])

    def test_health_check_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["environment"], "development")
        self.assertEqual(data["project"], "FinPilot AI")

    def test_api_v1_health_check_endpoint(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")

if __name__ == "__main__":
    unittest.main()
