from decimal import Decimal
import unittest
import uuid

from app.agent.monitoring_agent import monitoring_agent_node
from app.agent.state import AgentState


class MonitoringAgentTestCase(unittest.TestCase):
    def test_01_monitoring_agent_execution_and_facts(self):
        state: AgentState = {
            "request_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "query": "What changed in my finances and is my current plan still realistic?",
            "intent": "monitoring_review",
            "routing_decision": "monitoring_agent",
            "financial_context": {
                "profile": {
                    "monthly_income": 6000.0,
                    "essential_expenses": 2500.0,
                    "monthly_debt_payment": 300.0,
                    "current_savings": 15000.0,
                    "indicators": {
                        "emergency_fund": {
                            "months_covered": 6.0,
                            "status_label": "adequate",
                        }
                    },
                },
                "expense_summary": {
                    "total_expenses": 3400.0,
                    "essential_spending": 2500.0,
                    "non_essential_spending": 900.0,
                    "transaction_count": 25,
                },
                "safe_to_spend": {"daily_safe_to_spend": 38.0},
                "financial_health_score": {"overall_score": 82.0, "grade": "A"},
                "budget_performance": {"overall_variance": 0.0},
                "goals_portfolio": {
                    "goals": [],
                    "is_portfolio_feasible": True,
                    "total_required_monthly": 0.0,
                },
                "salary_plan": {"recurring_commitments": []},
            },
            "agent_response": "",
            "financial_facts": [],
            "recommendations": [],
            "execution_trace": [],
        }

        result = monitoring_agent_node(state)

        self.assertIn("Financial Monitoring Report", result["agent_response"])
        self.assertTrue(len(result["financial_facts"]) >= 3)
        self.assertTrue(len(result["execution_trace"]) >= 4)

        trace_steps = [s["step"] for s in result["execution_trace"]]
        self.assertIn("monitoring_started", trace_steps)
        self.assertIn("baseline_loaded", trace_steps)
        self.assertIn("current_state_built", trace_steps)
        self.assertIn("financial_changes_detected", trace_steps)
        self.assertIn("replanning_assessment_started", trace_steps)

        # Check monitoring snapshot in state
        self.assertIn("monitoring_snapshot", result)
        self.assertIn("replanning_assessment", result)
        self.assertIn("financial_changes", result)


if __name__ == "__main__":
    unittest.main()
