import unittest

from app.main import app
from app.rag.ingestion import KnowledgeIngestionPipeline
from app.agent.reflection import ReflectionValidator
from tests.test_helpers import create_test_env


class AgenticAcademicFeaturesTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine, cls.TestingSessionLocal, cls.test_user, cls.client = create_test_env(app, "academic_test@finpilot.ai")

        # Ingest datasets into testing database
        db = cls.TestingSessionLocal()
        try:
            pipeline = KnowledgeIngestionPipeline()
            pipeline.ingest_all_datasets(db)
        finally:
            db.close()

        # Set up a base profile
        prof_payload = {
            "monthly_income": 120000.00,
            "current_savings": 450000.00,
            "monthly_debt_payment": 25000.00,
            "essential_expenses": 50000.00,
            "dependents": 1,
            "emergency_savings": 300000.00,
            "risk_preference": "moderate",
        }
        cls.client.post("/api/v1/profile", json=prof_payload)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        cls.engine.dispose()

    def test_01_rag_sources_endpoint(self):
        response = self.client.get("/api/v1/rag/sources")
        self.assertEqual(response.status_code, 200)
        sources = response.json()
        self.assertIsInstance(sources, list)
        self.assertGreaterEqual(len(sources), 1)
        titles = [s["title"] for s in sources]
        self.assertTrue(any("RBI" in t or "SEBI" in t or "Tax" in t or "Debt" in t for t in titles))

    def test_02_rag_query_endpoint(self):
        payload = {
            "query": "What is the recommended emergency fund size for Indian households?",
            "top_k": 3,
        }
        response = self.client.post("/api/v1/rag/query", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("citations", data)
        self.assertIn("chunks", data)
        self.assertGreaterEqual(len(data["chunks"]), 1)

    def test_03_reflection_validator(self):
        validator = ReflectionValidator()
        financial_facts = [
            {"name": "Monthly Income", "value": "₹1,20,000"},
            {"name": "Current Savings", "value": "₹4,50,000"},
        ]
        raw_text = "Your monthly income is ₹1,20,000 and you have ₹4,50,000 in liquid savings."
        audit = validator.audit_and_correct(
            draft_content=raw_text,
            verified_facts=financial_facts,
            rag_citations=[{"title": "RBI Guide"}],
            user_query="How are my savings?",
        )
        self.assertEqual(audit["status"], "passed")
        self.assertGreaterEqual(audit["groundedness_score"], 0.9)

        # Test currency correction ($ -> ₹)
        dollar_text = "You can save $5,000 every month."
        corrected_audit = validator.audit_and_correct(
            draft_content=dollar_text,
            verified_facts=[],
        )
        self.assertEqual(corrected_audit["status"], "corrected")
        self.assertIn("₹5,000", corrected_audit["final_content"])

    def test_04_hitl_review_endpoint(self):
        review_payload = {
            "action": "accepted",
            "agent_name": "Spending Analyst Agent",
            "user_notes": "Agreed, will trim dining out budget by ₹3,000.",
        }
        response = self.client.post("/api/v1/hitl/recommendations/rec-test-101/review", json=review_payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["action"], "accepted")

        # Fetch reviews
        reviews_resp = self.client.get("/api/v1/hitl/reviews")
        self.assertEqual(reviews_resp.status_code, 200)
        reviews = reviews_resp.json()
        self.assertGreaterEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["recommendation_id"], "rec-test-101")

    def test_05_agent_lab_registry(self):
        response = self.client.get("/api/v1/agent-lab/agents")
        self.assertEqual(response.status_code, 200)
        agents = response.json()
        self.assertIsInstance(agents, list)
        self.assertGreaterEqual(len(agents), 6)
        agent_ids = [a["id"] for a in agents]
        self.assertIn("orchestrator", agent_ids)
        self.assertIn("spending_analyst", agent_ids)
        self.assertIn("decision_agent", agent_ids)
        self.assertIn("planning_agent", agent_ids)
        self.assertIn("monitoring_agent", agent_ids)
        self.assertIn("replanning_agent", agent_ids)

    def test_06_agent_lab_run_agent(self):
        payload = {
            "agent_id": "spending_analyst",
            "query": "How can I cut dining expenses and save ₹5,000 more per month?",
        }
        response = self.client.post("/api/v1/agent-lab/run-agent", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent_id"], "spending_analyst")
        self.assertIn("final_response", data)
        self.assertIn("execution_trace", data)
        self.assertIn("rag_citations", data)
        self.assertIn("reflection_audit", data)

    def test_07_agent_lab_run_multi_agent_workflow(self):
        payload = {
            "workflow_id": "spending_decision_planning",
            "query": "My food delivery costs rose by ₹7,000 this month. Should I reallocate or adjust my vacation fund?",
        }
        response = self.client.post("/api/v1/agent-lab/run-workflow", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["workflow_id"], "spending_decision_planning")
        self.assertIn("final_response", data)
        self.assertIn("execution_trace", data)
        self.assertGreaterEqual(len(data["execution_trace"]), 2)

    def test_08_evaluation_rag_comparison_endpoint(self):
        response = self.client.get("/api/v1/evaluation/rag-comparison?dataset_name=rag_questions.jsonl")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("no_rag", data)
        self.assertIn("basic_rag", data)
        self.assertIn("agentic_rag", data)
        self.assertIn("comparative_insights", data)
        self.assertGreater(data["agentic_rag"]["groundedness_score"], data["no_rag"]["groundedness_score"])

    def test_09_evaluation_llm_benchmark_endpoint(self):
        response = self.client.get("/api/v1/evaluation/llm-benchmark")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("models", data)
        self.assertIn("benchmarked_dataset", data)
        self.assertGreaterEqual(len(data["models"]), 2)
