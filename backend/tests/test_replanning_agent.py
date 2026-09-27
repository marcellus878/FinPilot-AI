from decimal import Decimal
import unittest
import uuid

from app.agent.replanning_agent import replanning_agent_node
from app.agent.state import AgentState


class ReplanningAgentTestCase(unittest.TestCase):
    def test_01_replanning_agent_execution_and_comparison(self):
        state: AgentState = {
            "request_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "query": "What should I adjust in my financial plan after this expense surge?",
            "intent": "plan_adaptation",
            "routing_decision": "replanning_agent",
            "financial_context": {
                "profile": {
                    "monthly_income": 5000.0,
                    "essential_expenses": 2800.0,
                    "monthly_debt_payment": 300.0,
                    "current_savings": 8000.0,
                    "indicators": {
                        "emergency_fund": {
                            "months_covered": 2.85,
                            "status_label": "vulnerable",
                        }
                    },
                },
                "expense_summary": {
                    "total_expenses": 4200.0,
                    "essential_spending": 2800.0,
                    "non_essential_spending": 1400.0,
                    "transaction_count": 30,
                },
                "safe_to_spend": {"daily_safe_to_spend": 5.0},
                "financial_health_score": {"overall_score": 62.0, "grade": "B"},
                "budget_performance": {"overall_variance": -300.0},
                "goals_portfolio": {
                    "goals": [
                        {
                            "name": "Emergency Fund",
                            "target_amount": 15000.0,
                            "current_amount": 8000.0,
                            "monthly_contribution": 500.0,
                        }
                    ],
                    "is_portfolio_feasible": False,
                    "total_required_monthly": 500.0,
                    "available_monthly_capacity": 300.0,
                },
                "salary_plan": {"recurring_commitments": []},
            },
            "agent_response": "",
            "financial_facts": [],
            "recommendations": [],
            "execution_trace": [],
            "replanning_assessment": {
                "replanning_required": True,
                "trigger": "spending_surge",
                "severity": "high",
                "reasons": ["Discretionary spending surged and safe-to-spend dropped"],
            },
        }

        result = replanning_agent_node(state)

        self.assertIn("Adaptive Financial Plan Proposal", result["agent_response"])
        self.assertTrue(len(result["financial_facts"]) >= 3)
        self.assertTrue(len(result["recommendations"]) >= 1)
        self.assertTrue(len(result["execution_trace"]) >= 4)

        trace_steps = [s["step"] for s in result["execution_trace"]]
        self.assertIn("replanning_started", trace_steps)
        self.assertIn("revised_plan_generated", trace_steps)
        self.assertIn("plan_comparison_generated", trace_steps)
        self.assertIn("monitoring_completed", trace_steps)

        # Check plan comparison and strategies in state
        self.assertIn("plan_comparison", result)
        self.assertTrue(len(result["plan_comparison"]["items"]) >= 5)
        self.assertIn("replanning_strategies", result)
        self.assertEqual(len(result["replanning_strategies"]), 4)


if __name__ == "__main__":
    unittest.main()
