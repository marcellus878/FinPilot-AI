from datetime import datetime
import re
from typing import Dict, Any

from app.agent.state import AgentState, AgentTraceStep


def classify_intent(query: str) -> str:
    """Classifies user query intent using robust pattern matching."""
    q = query.lower().strip()
    
    # 1. Decision Memory & Historical Lookups
    if any(k in q for k in [
        "what did i decide", "did i decide", "previous decision", "past decision",
        "my previous", "what was my decision", "have i previously", "reconsider my",
        "changed since my last", "since this decision", "revisit my decision",
        "what did i plan for"
    ]):
        return "memory_query"

    # 2. Proactive Insights
    if any(k in q for k in [
        "proactive", "insight", "financial opportunities", "review my opportunities",
        "what should i reconsider", "financial blindspots"
    ]):
        return "proactive_insights"

    # 3. Monitoring & Adaptive Replanning patterns
    if any(k in q for k in [
        "what changed", "what has changed", "changes in my finances",
        "is my plan realistic", "is my current plan still realistic",
        "why did my plan change", "which goal is affected", "what should i adjust",
        "adjust after this unexpected", "monitor my", "monitoring", "plan adaptation",
        "replan", "plan needs attention", "check my plan"
    ]):
        return "monitoring_review"

    # 4. Decision / Affordability / Scenario Evaluation patterns
    if any(k in q for k in [
        "can i afford", "should i buy", "afford", "can i spend",
        "what happens if i take", "what happens if my salary",
        "will this purchase", "take this emi", "take a loan", "buy a",
        "affordability", "scenario", "simulate", "purchase a",
        "increase this recurring", "salary decrease", "pay cut"
    ]):
        return "decision_evaluation"

    # 5. Financial Plan & Salary Allocation patterns
    if any(k in q for k in [
        "allocate my salary", "how should i allocate", "salary allocation",
        "reach my", "save for a", "plan my salary", "distribute my salary",
        "allocation plan", "competing goals", "goal conflict", "safe to spend",
        "cash flow", "payday"
    ]):
        return "financial_plan"

    # 6. Spending Analysis patterns
    if any(k in q for k in [
        "spending", "spent", "where does my money", "where did my money",
        "category", "categories", "discretionary", "habit", "unusual",
        "leak", "dining", "entertainment", "groceries", "breakdown"
    ]):
        return "spending_analysis"
    
    # 7. Expense Reduction patterns
    if any(k in q for k in [
        "cut expense", "cut cost", "save money", "reduce expense", "reduce cost",
        "lower bill", "subscription", "recurring", "cancel", "optimize expense",
        "trim", "tighten", "cut spending"
    ]):
        return "expense_reduction"

    # 8. Goal Planning patterns
    if any(k in q for k in [
        "goal", "target", "milestone", "timeline", "conflict",
        "vacation fund", "house down payment", "emergency fund target", "college fund"
    ]):
        return "goal_planning"

    return "general_financial_question"


def select_agent_chain(intent: str, query: str) -> list:
    """
    Determines the ordered sequence of agents required for the query.
    Enables sequential multi-agent execution when appropriate.
    """
    q = query.lower()
    
    # Compound: Spending + Goal/Planning question
    if intent == "spending_analysis" and any(k in q for k in ["goal", "affect", "impact", "target", "afford"]):
        return ["spending_analyst", "planning_agent"]

    # Compound: Monitoring + Replanning + Planning
    if intent in ["monitoring_review", "plan_adaptation"]:
        return ["monitoring_agent"]

    if intent == "decision_evaluation":
        return ["decision_agent"]

    if intent in ["financial_plan", "goal_planning"]:
        return ["planning_agent"]

    if intent == "spending_analysis":
        return ["spending_analyst"]

    if intent == "expense_reduction":
        return ["expense_reduction"]

    return ["general_advisor"]


def orchestrator_node(state: AgentState) -> Dict[str, Any]:
    """
    Multi-Agent Orchestrator node:
    1. Analyzes user query & classified intent
    2. Selects appropriate agent execution chain
    3. Initializes multi-agent lifecycle state
    4. Logs structured orchestration trace step
    """
    query = state.get("query", "")
    intent = classify_intent(query)
    agent_chain = select_agent_chain(intent, query)
    first_agent = agent_chain[0] if agent_chain else "general_advisor"

    trace_step: AgentTraceStep = {
        "step": "agents_selected",
        "agent": "Orchestrator",
        "action": f"Selected multi-agent chain: {' -> '.join(agent_chain)} for intent '{intent}'",
        "details": {
            "query": query,
            "classified_intent": intent,
            "selected_agents": agent_chain,
            "initial_routing": first_agent,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    current_trace = list(state.get("execution_trace", []))
    current_trace.append(trace_step)

    return {
        "intent": intent,
        "selected_agents": agent_chain,
        "agent_chain": agent_chain,
        "current_agent": first_agent,
        "agent_step_index": 0,
        "routing_decision": first_agent,
        "execution_trace": current_trace,
    }

