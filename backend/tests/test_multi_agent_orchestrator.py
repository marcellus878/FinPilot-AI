import uuid
from decimal import Decimal
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agent.graph import advisor_graph, run_advisor_agent
from app.agent.orchestrator import classify_intent, select_agent_chain
from app.agent.state import AgentState
from app.agent.validator import validate_agent_output, validate_financial_facts, validate_recommendations
from app.core.database import Base
from app.models.financial_profile import FinancialProfile
from app.models.user import User


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_user(db_session):
    user = User(
        id=uuid.uuid4(),
        email="orchestrator_test@finpilot.ai",
        full_name="Orchestrator Test User",
    )
    db_session.add(user)
    db_session.commit()

    profile = FinancialProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        monthly_income=Decimal("5000.00"),
        current_savings=Decimal("12000.00"),
        monthly_debt_payment=Decimal("300.00"),
        essential_expenses=Decimal("2200.00"),
        emergency_savings=Decimal("10000.00"),
        dependents=0,
        risk_preference="moderate",
    )
    db_session.add(profile)
    db_session.commit()
    return user


class TestMultiAgentOrchestrator:
    def test_01_intent_classification_and_chain_selection(self):
        # 1. Single agent selection
        intent1 = classify_intent("Can I afford to buy a $1,200 smartphone?")
        assert intent1 == "decision_evaluation"
        chain1 = select_agent_chain(intent1, "Can I afford to buy a $1,200 smartphone?")
        assert chain1 == ["decision_agent"]

        # 2. Compound multi-agent selection (spending + goal impact)
        query2 = "I spent much more on dining this month. Will this affect my vacation goal?"
        intent2 = classify_intent(query2)
        assert intent2 == "spending_analysis"
        chain2 = select_agent_chain(intent2, query2)
        assert chain2 == ["spending_analyst", "planning_agent"]

        # 3. Memory lookup intent
        intent3 = classify_intent("What did I decide previously about my laptop purchase?")
        assert intent3 == "memory_query"

    def test_02_validator_layer(self):
        context = {
            "profile": {"monthly_income": 5000.0, "current_savings": 12000.0, "essential_expenses": 2200.0},
            "core_metrics": {"disposable_income": 2500.0, "savings_rate": 50.0, "emergency_fund_months": 4.5},
            "expenses": {"total_expenses": 2500.0},
            "cash_flow_planning": {"safe_to_spend_daily": 40.0},
        }

        # Valid facts & recommendations
        valid_facts = [{"metric": "Monthly Income", "value": "$5,000.00"}]
        valid_recs = [{"title": "Cut Subscriptions", "description": "Audit streaming services", "potential_monthly_savings": 25.0}]
        state = {
            "financial_facts": valid_facts,
            "recommendations": valid_recs,
            "financial_context": context,
            "agent_response": "Everything looks good.",
        }
        is_valid, errors = validate_agent_output(state)
        assert is_valid is True
        assert len(errors) == 0

        # Invalid facts (missing metric)
        invalid_facts = [{"value": 100}]
        facts_ok, fact_errs = validate_financial_facts(invalid_facts, context)
        assert facts_ok is False
        assert len(fact_errs) > 0

    def test_03_autonomous_multi_agent_execution(self, db_session, sample_user):
        # Run compound query through end-to-end multi-agent pipeline
        query = "Where did my money go and how does it affect my goal budget?"
        result_state = run_advisor_agent(db_session, sample_user.id, query)

        assert result_state is not None
        assert "execution_trace" in result_state
        trace_steps = [s.get("step") for s in result_state["execution_trace"]]
        
        # Verify orchestration sequence
        assert "agents_selected" in trace_steps
        assert "memory_lookup_started" in trace_steps
        assert "memory_lookup_completed" in trace_steps
        assert "validation_started" in trace_steps
        assert "validation_passed" in trace_steps
        assert len(result_state.get("financial_facts", [])) > 0
