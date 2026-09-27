from decimal import Decimal
import unittest
import uuid

from app.agent.decision_agent import (
    decision_agent_node,
    execute_decision_pipeline,
    extract_decision_parameters,
)
from app.agent.state import AgentState
from app.schemas.decision import DecisionRequest


class DecisionAgentTestCase(unittest.TestCase):
    def test_01_parameter_extraction_one_time_purchase(self):
        query = "Can I afford to buy a $2,500 laptop?"
        req = extract_decision_parameters(query)
        self.assertEqual(req.decision_type, "one_time_purchase")
        self.assertEqual(req.amount, Decimal("2500.00"))
        self.assertEqual(req.description, "Laptop")

    def test_02_parameter_extraction_recurring_emi(self):
        query = "Can I take on a 500 per month car loan for 36 months?"
        req = extract_decision_parameters(query)
        self.assertEqual(req.decision_type, "new_recurring_expense")
        self.assertEqual(req.amount, Decimal("500.00"))
        self.assertEqual(req.description, "Car")
        self.assertEqual(req.duration_months, 36)

    def test_03_parameter_extraction_income_change(self):
        query = "What happens if I get a 1000 salary increase?"
        req = extract_decision_parameters(query)
        self.assertEqual(req.decision_type, "income_change")
        self.assertEqual(req.amount, Decimal("1000.00"))

        query_drop = "What if I suffer a 1500 salary cut?"
        req_drop = extract_decision_parameters(query_drop)
        self.assertEqual(req_drop.decision_type, "income_change")
        self.assertEqual(req_drop.amount, Decimal("-1500.00"))

    def test_04_parameter_extraction_unexpected_expense(self):
        query = "Can my emergency fund handle an unexpected 3500 medical bill?"
        req = extract_decision_parameters(query)
        self.assertEqual(req.decision_type, "unexpected_expense")
        self.assertEqual(req.amount, Decimal("3500.00"))
        self.assertEqual(req.description, "Medical Bill")

    def test_05_execute_decision_pipeline_deterministic(self):
        req = DecisionRequest(
            decision_type="one_time_purchase",
            amount=Decimal("3000.00"),
            description="MacBook Pro",
            timing_months=0,
        )
        context = {
            "profile": {
                "monthly_income": 6000.0,
                "essential_expenses": 2500.0,
                "monthly_debt_payment": 300.0,
                "current_savings": 15000.0,
            },
            "goals_portfolio": {
                "goals": [
                    {
                        "id": "goal-1",
                        "name": "House Downpayment",
                        "target_amount": 50000.0,
                        "current_amount": 10000.0,
                        "monthly_contribution": 1000.0,
                    }
                ]
            },
        }

        scenario_res, dec_result = execute_decision_pipeline(req, context)

        # Verify deterministic scenario output
        self.assertIn(scenario_res.affordability_verdict, ["safe", "stretched", "unaffordable"])
        self.assertEqual(scenario_res.after_state.current_savings, Decimal("12000.00"))
        self.assertEqual(scenario_res.delta.savings_delta, Decimal("-3000.00"))

        # Verify structured DecisionResult
        self.assertIn("Verdict:", dec_result.summary)
        self.assertTrue(len(dec_result.financial_facts) >= 4)
        self.assertTrue(len(dec_result.impacts) >= 4)
        self.assertTrue(len(dec_result.options) >= 2)
        self.assertEqual(dec_result.confidence, "high")

    def test_06_decision_agent_node_execution(self):
        state: AgentState = {
            "session_id": "test-session",
            "user_id": str(uuid.uuid4()),
            "query": "Can I afford to buy a 2000 dollar laptop?",
            "intent": "decision_evaluation",
            "routing_decision": "decision_agent",
            "financial_context": {
                "profile": {
                    "monthly_income": 5000.0,
                    "essential_expenses": 2000.0,
                    "monthly_debt_payment": 0.0,
                    "current_savings": 10000.0,
                },
                "goals_portfolio": {"goals": []},
            },
            "agent_response": "",
            "financial_facts": [],
            "recommendations": [],
            "execution_trace": [],
        }

        result = decision_agent_node(state)

        self.assertIn("Decision Assessment", result["agent_response"])
        self.assertTrue(len(result["financial_facts"]) >= 3)
        self.assertTrue(len(result["recommendations"]) >= 1)
        self.assertTrue(len(result["execution_trace"]) >= 4)

        trace_steps = [t["step"] for t in result["execution_trace"]]
        self.assertIn("decision_parameters_extracted", trace_steps)
        self.assertIn("scenario_calculated", trace_steps)
        self.assertIn("decision_analysis_started", trace_steps)
        self.assertIn("decision_analysis_completed", trace_steps)


if __name__ == "__main__":
    unittest.main()
