from datetime import date
from decimal import Decimal
import unittest
import uuid

from app.agent.planning_agent import planning_agent_node
from app.agent.state import AgentState


class PlanningAgentTestCase(unittest.TestCase):
    def test_01_salary_allocation_planning(self):
        state: AgentState = {
            "session_id": "test-session-plan",
            "user_id": str(uuid.uuid4()),
            "query": "How should I allocate my monthly salary and what is my safe to spend?",
            "intent": "financial_plan",
            "routing_decision": "planning_agent",
            "financial_context": {
                "profile": {
                    "monthly_income": 6000.0,
                    "essential_expenses": 2500.0,
                    "monthly_debt_payment": 500.0,
                    "current_savings": 12000.0,
                },
                "goals_portfolio": {"goals": []},
            },
            "agent_response": "",
            "financial_facts": [],
            "recommendations": [],
            "execution_trace": [],
        }

        result = planning_agent_node(state)

        self.assertIn("Structured Financial Plan & Salary Allocation", result["agent_response"])
        self.assertTrue(len(result["financial_facts"]) >= 3)
        self.assertTrue(len(result["recommendations"]) >= 1)
        self.assertTrue(len(result["execution_trace"]) >= 2)

        trace_steps = [t["step"] for t in result["execution_trace"]]
        self.assertIn("planning_analysis_started", trace_steps)
        self.assertIn("planning_analysis_completed", trace_steps)

    def test_02_competing_goals_conflict_resolution(self):
        state: AgentState = {
            "session_id": "test-session-goals",
            "user_id": str(uuid.uuid4()),
            "query": "I have competing goals for emergency fund and house downpayment, how do I resolve the conflict?",
            "intent": "goal_planning",
            "routing_decision": "planning_agent",
            "financial_context": {
                "profile": {
                    "monthly_income": 7000.0,
                    "essential_expenses": 3000.0,
                    "monthly_debt_payment": 500.0,
                    "current_savings": 15000.0,
                },
                "goals_portfolio": {
                    "goals": [
                        {
                            "id": "goal-1",
                            "name": "Emergency Fund",
                            "target_amount": 20000.0,
                            "current_amount": 10000.0,
                            "monthly_contribution": 1000.0,
                            "target_date": "2026-12-31",
                        },
                        {
                            "id": "goal-2",
                            "name": "Downpayment",
                            "target_amount": 50000.0,
                            "current_amount": 5000.0,
                            "monthly_contribution": 1500.0,
                            "target_date": "2027-12-31",
                        },
                    ]
                },
            },
            "agent_response": "",
            "financial_facts": [],
            "recommendations": [],
            "execution_trace": [],
        }

        result = planning_agent_node(state)

        # Verify that goal conflict strategies were calculated & presented
        self.assertIn("Competing Goal Strategies", result["agent_response"])
        self.assertIn("Priority Waterfall", result["agent_response"])
        self.assertIn("Proportional Progress", result["agent_response"])
        self.assertIn("Equal Split", result["agent_response"])

        rec_titles = [r["title"] for r in result["recommendations"]]
        self.assertTrue(any("Waterfall" in t or "Strategy" in t or "Salary Allocation" in t for t in rec_titles))


if __name__ == "__main__":
    unittest.main()
