import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.security import get_current_user
from app.agent.graph import run_advisor_agent
from app.core.database import get_db
from app.models.user import User

router = APIRouter()

AGENT_REGISTRY = [
    {
        "id": "orchestrator",
        "name": "Orchestrator Agent",
        "role": "Multi-Agent Coordinator & Intent Classifier",
        "icon": "Layers",
        "purpose": "Classifies incoming financial queries, selects single or multi-agent execution graphs, and coordinates tool execution.",
        "inputs": ["User Natural Language Query", "Financial Profile", "Recent Transactions", "Decision History"],
        "tools": ["Intent Classifier", "Context Builder", "RAG Need Evaluator", "Graph Router"],
        "memory_access": "PostgreSQL Decision History + LangGraph Execution State",
        "workflow_steps": [
            "Perceive Query & Intent",
            "Evaluate RAG Knowledge Need",
            "Retrieve Decision Memory",
            "Dispatch Specialized Agent Chain",
            "Validate & Reflect on Output",
        ],
        "sample_prompts": [
            "Review my entire financial plan and highlight optimization opportunities.",
            "Can I afford a ₹60,000 laptop while maintaining my emergency fund?",
        ],
    },
    {
        "id": "spending_analyst",
        "name": "Spending Analyst Agent",
        "role": "Transaction Anomaly & Categorization Specialist",
        "icon": "TrendingDown",
        "purpose": "Audits transaction streams, quantifies essential vs discretionary burn rates, and detects micro-spending leaks.",
        "inputs": ["Transaction Ledger", "Category Budgets", "Essentiality Tags"],
        "tools": ["Spending Intelligence Engine", "Anomaly Detector", "Recurring Commitment Normalizer"],
        "memory_access": "Past Spending Baselines & Anomaly History",
        "workflow_steps": [
            "Ingest Transactions",
            "Classify Essentiality",
            "Detect Category Spikes",
            "Cluster Recurring Leaks",
            "Formulate Trimming Insights",
        ],
        "sample_prompts": [
            "Analyze where my discretionary spending went this month.",
            "Find recurring subscription leaks in my ledger.",
        ],
    },
    {
        "id": "expense_reduction",
        "name": "Expense Reduction Agent",
        "role": "Tactical Discretionary Trimming Engine",
        "icon": "Scissors",
        "purpose": "Identifies high-impact discretionary expense cuts without compromising essential obligations or lifestyle floor.",
        "inputs": ["Discretionary Spending Breakdown", "Subscriptions", "Budget Variances"],
        "tools": ["Expense Trimming Optimizer", "Subscription Analyzer"],
        "memory_access": "Previous Expense Trimming Recommendations",
        "workflow_steps": [
            "Scan Discretionary Categories",
            "Isolate Non-Essential Spikes",
            "Calculate Potential Monthly Savings",
            "Generate Actionable Reduction Cards",
        ],
        "sample_prompts": [
            "How can I cut ₹5,000 from my monthly expenses?",
            "Optimize my entertainment and dining out budget.",
        ],
    },
    {
        "id": "decision_agent",
        "name": "Decision Intelligence Agent",
        "role": "Counterfactual Simulation & Trade-off Analyzer",
        "icon": "Scale",
        "purpose": "Evaluates large one-time purchases, loans, and commitments using 3-step affordability tests and trade-off synthesis.",
        "inputs": ["Purchase Amount", "Timing", "Liquid Savings", "Monthly Surplus", "Active Goals"],
        "tools": ["Scenario Engine", "Emergency Runway Calculator", "Goal Timeline Delay Simulator", "RAG Retriever"],
        "memory_access": "Historical Decision Records & Strategy Alternatives",
        "workflow_steps": [
            "Parse Purchase Parameters",
            "Run Multi-Factor Counterfactual Simulation",
            "Check 3-Month Emergency Runway Floor",
            "Evaluate Goal Delays",
            "Synthesize Balanced Mitigation Alternatives",
        ],
        "sample_prompts": [
            "Can I afford to buy a ₹60,000 laptop right now?",
            "Can I take on a ₹15,000 per month car loan for 36 months?",
        ],
    },
    {
        "id": "planning_agent",
        "name": "Planning Agent",
        "role": "Salary Allocation & Goal Conflict Resolver",
        "icon": "Target",
        "purpose": "Applies 50/30/20 proportional allocation, sizes emergency reserves, and resolves competing goal priority deficits.",
        "inputs": ["Monthly Inflow", "Fixed Commitments", "Goal Targets & Deadlines"],
        "tools": ["50/30/20 Allocation Engine", "Goal Conflict Resolver", "Safe-to-Spend Calculator", "RAG Retriever"],
        "memory_access": "Baseline Financial Plan & Target Goal Timelines",
        "workflow_steps": [
            "Calculate Proportional Inflow Distribution",
            "Ring-fence Essential Commitments",
            "Assess Goal Deficits by Priority Tier",
            "Propose Timeline Extensions or Pro-rata Scaling",
        ],
        "sample_prompts": [
            "How should I allocate my ₹75,000 monthly salary?",
            "I have competing goals for Emergency Fund and House Downpayment, resolve conflict.",
        ],
    },
    {
        "id": "monitoring_agent",
        "name": "Monitoring Agent",
        "role": "Continuous Financial Drift Surveillance",
        "icon": "Activity",
        "purpose": "Quantifies variances between live financial metrics and baseline plan targets, detecting financial shocks.",
        "inputs": ["Live Income", "Spending Burn Rate", "Emergency Reserve Level", "Goal Progress"],
        "tools": ["Monitoring Engine", "Variance Detector", "Trigger Evaluator"],
        "memory_access": "Baseline Plan Snapshot & Trigger Thresholds",
        "workflow_steps": [
            "Build Current Quantized Snapshot",
            "Compare Against Baseline Plan",
            "Quantify Absolute & Percentage Deltas",
            "Evaluate Replanning Trigger Conditions",
        ],
        "sample_prompts": [
            "Review my plan health and check for financial drift.",
            "Run live surveillance diagnostic on my budget.",
        ],
    },
    {
        "id": "replanning_agent",
        "name": "Adaptive Replanning Agent",
        "role": "Non-Destructive Plan Adaptation Synthesizer",
        "icon": "RefreshCw",
        "purpose": "Generates side-by-side Before vs After plan comparisons and non-destructive recovery strategy options during financial shocks.",
        "inputs": ["Drift Severity", "Affected Goals", "Deficit Magnitude", "Income Change"],
        "tools": ["Replanning Strategy Generator", "Plan Comparison Matrix Engine", "RAG Retriever"],
        "memory_access": "Historical Adaptation Events",
        "workflow_steps": [
            "Ingest Detected Drift Triggers",
            "Simulate Plan Recovery Paths",
            "Construct Before vs After Comparison Table",
            "Generate Distinct Tradeoff Strategy Options",
        ],
        "sample_prompts": [
            "My income dropped by 10%, synthesize an adaptive recovery plan.",
            "My rent increased by ₹5,000, how should my plan adapt?",
        ],
    },
    {
        "id": "general_advisor",
        "name": "General Financial Advisor",
        "role": "Holistic Financial Planning & Advisory",
        "icon": "Sparkles",
        "purpose": "Provides grounded financial literacy, guidance on Indian savings instruments, and holistic advisory synthesis.",
        "inputs": ["Comprehensive Financial State", "RBI / SEBI Guidelines"],
        "tools": ["RAG Knowledge Retriever", "Financial Context Builder", "Reflection Engine"],
        "memory_access": "Full User Financial Profile & Decision History",
        "workflow_steps": [
            "Synthesize Complete Profile State",
            "Query Authoritative Knowledge Base",
            "Formulate Actionable Recommendations",
            "Validate Groundedness & Accuracy",
        ],
        "sample_prompts": [
            "What is the RBI guideline on emergency fund sizing?",
            "What proactive optimizations should I look into right now?",
        ],
    },
]


class RunAgentIn(BaseModel):
    agent_id: str
    query: str


class RunMultiAgentWorkflowIn(BaseModel):
    workflow_id: str  # "spending_decision_planning" or "monitoring_replanning_planning"
    query: str


@router.get("/agents")
def get_agent_registry():
    """Return catalog of all 8 specialized agents with their roles, tools, and workflows."""
    return AGENT_REGISTRY


@router.post("/run-agent")
def run_individual_agent(
    payload: RunAgentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Run an agent directly in the Agent Lab sandbox with complete inspection:
    - Verified Facts from Financial Engine
    - Retrieved RAG Citations
    - Execution Trace
    - Reflection & Self-Correction Status
    - Actionable Recommendations with HITL review capability
    """
    state = run_advisor_agent(
        db=db,
        user_id=current_user.id,
        query=payload.query,
    )

    return {
        "agent_id": payload.agent_id,
        "query": payload.query,
        "intent": state.get("intent"),
        "selected_agents": state.get("selected_agents", []),
        "agent_chain": state.get("agent_chain", []),
        "final_response": state.get("final_response"),
        "financial_facts": state.get("financial_facts", []),
        "rag_citations": state.get("rag_citations", []),
        "recommendations": state.get("recommendations", []),
        "reflection_audit": state.get("reflection_audit"),
        "execution_trace": state.get("execution_trace", []),
        "prompt_versions": state.get("prompt_versions", {}),
    }


@router.post("/run-workflow")
def run_multi_agent_workflow(
    payload: RunMultiAgentWorkflowIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute an explicit multi-agent collaborative journey:
    - Workflow 1: Spending Anomaly -> Decision Agent -> Goal Planning
    - Workflow 2: Monitoring Shock -> Replanning Agent -> Planning Agent
    """
    state = run_advisor_agent(
        db=db,
        user_id=current_user.id,
        query=payload.query,
    )

    return {
        "workflow_id": payload.workflow_id,
        "query": payload.query,
        "selected_agents": state.get("selected_agents", []),
        "agent_chain": state.get("agent_chain", []),
        "final_response": state.get("final_response"),
        "financial_facts": state.get("financial_facts", []),
        "rag_citations": state.get("rag_citations", []),
        "recommendations": state.get("recommendations", []),
        "reflection_audit": state.get("reflection_audit"),
        "execution_trace": state.get("execution_trace", []),
    }
