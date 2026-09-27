from datetime import date, datetime
from decimal import Decimal
import unittest
import uuid

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.agent.graph import run_advisor_agent
from app.agent.orchestrator import classify_intent
from app.core.database import Base
from app.models.agent_event import AgentEvent
from app.models.financial_profile import FinancialProfile
from app.models.transaction import Transaction
from app.models.user import User


class AgentGraphTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.Session = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self):
        self.db = self.Session()
        self.user_id = uuid.uuid4()
        user = User(id=self.user_id, email=f"graph_{self.user_id}@example.com", full_name="Graph Test User")
        self.db.add(user)
        
        profile = FinancialProfile(
            user_id=self.user_id,
            monthly_income=Decimal("6000.00"),
            current_savings=Decimal("18000.00"),
            monthly_debt_payment=Decimal("300.00"),
            essential_expenses=Decimal("2800.00"),
            emergency_savings=Decimal("15000.00"),
            dependents=1,
            risk_preference="moderate",
        )
        self.db.add(profile)

        # Add transactions including recurring & misc
        t1 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            amount=Decimal("150.00"),
            type="expense",
            category="Food & Dining",
            description="Restaurants",
            transaction_date=datetime.now(),
        )
        t2 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            amount=Decimal("80.00"),
            type="expense",
            category="Entertainment",
            description="Gym subscription",
            transaction_date=datetime.now(),
        )
        t3 = Transaction(
            id=uuid.uuid4(),
            user_id=self.user_id,
            amount=Decimal("120.00"),
            type="expense",
            category="Other",
            description="Misc miscellaneous leak",
            transaction_date=datetime.now(),
        )
        self.db.add_all([t1, t2, t3])
        self.db.commit()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_01_intent_classification(self):
        self.assertEqual(classify_intent("Where did my money go this month?"), "spending_analysis")
        self.assertEqual(classify_intent("How can I cut expenses and reduce subscriptions?"), "expense_reduction")
        self.assertEqual(classify_intent("What is my safe to spend limit today?"), "financial_plan")
        self.assertEqual(classify_intent("Can I afford to buy a 2000 dollar laptop?"), "decision_evaluation")
        self.assertEqual(classify_intent("How is my emergency fund target goal progressing?"), "goal_planning")
        self.assertEqual(classify_intent("Hello, what are some financial tips?"), "general_financial_question")

    def test_02_spending_analyst_execution(self):
        state = run_advisor_agent(
            db=self.db,
            user_id=self.user_id,
            query="Analyze my discretionary spending and category breakdown",
        )

        self.assertEqual(state["intent"], "spending_analysis")
        self.assertEqual(state["routing_decision"], "spending_analyst")
        self.assertIn("Spending Intelligence Analysis", state["agent_response"])
        self.assertTrue(len(state["financial_facts"]) > 0)
        self.assertTrue(len(state["execution_trace"]) >= 2)

        # Check AgentEvent recorded in DB
        events = list(self.db.scalars(select(AgentEvent).where(AgentEvent.user_id == self.user_id)).all())
        self.assertTrue(len(events) >= 1)
        self.assertEqual(events[-1].responsible_agent, "spending_analyst")

    def test_03_expense_reduction_execution(self):
        state = run_advisor_agent(
            db=self.db,
            user_id=self.user_id,
            query="How can I cut expenses and save more money?",
        )

        self.assertEqual(state["intent"], "expense_reduction")
        self.assertEqual(state["routing_decision"], "expense_reduction")
        self.assertIn("Expense Reduction", state["agent_response"])
        self.assertTrue(len(state["recommendations"]) > 0)

    def test_04_general_advisor_execution(self):
        state = run_advisor_agent(
            db=self.db,
            user_id=self.user_id,
            query="What is my general financial status?",
        )

        self.assertEqual(state["routing_decision"], "general_advisor")
        self.assertTrue(len(state["financial_facts"]) > 0)

    def test_05_decision_agent_execution(self):
        state = run_advisor_agent(
            db=self.db,
            user_id=self.user_id,
            query="Can I afford to buy a 2500 dollar laptop?",
        )

        self.assertEqual(state["intent"], "decision_evaluation")
        self.assertEqual(state["routing_decision"], "decision_agent")
        self.assertIn("Decision Assessment", state["agent_response"])
        self.assertTrue(len(state["financial_facts"]) > 0)
        self.assertTrue(len(state["execution_trace"]) >= 4)

        # Check AgentEvent recorded in DB
        events = list(self.db.scalars(select(AgentEvent).where(AgentEvent.user_id == self.user_id)).all())
        self.assertTrue(any(e.responsible_agent == "decision_agent" for e in events))

    def test_06_planning_agent_execution(self):
        state = run_advisor_agent(
            db=self.db,
            user_id=self.user_id,
            query="How should I allocate my monthly salary across my savings and goals?",
        )

        self.assertEqual(state["intent"], "financial_plan")
        self.assertEqual(state["routing_decision"], "planning_agent")
        self.assertIn("Structured Financial Plan", state["agent_response"])
        self.assertTrue(len(state["financial_facts"]) > 0)

    def test_07_monitoring_agent_execution(self):
        state = run_advisor_agent(
            db=self.db,
            user_id=self.user_id,
            query="What changed in my finances and is my current plan still realistic?",
        )

        self.assertEqual(state["intent"], "monitoring_review")
        self.assertEqual(state["routing_decision"], "monitoring_agent")
        self.assertIn("Financial Monitoring Report", state["agent_response"])
        self.assertTrue(len(state["financial_facts"]) > 0)
        self.assertTrue(len(state["execution_trace"]) >= 4)


if __name__ == "__main__":
    unittest.main()
