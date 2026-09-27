from datetime import datetime
from typing import Any, Dict, List
import uuid

from app.agent.llm import execute_llm_reasoning
from app.agent.state import AgentRecommendation, AgentState, AgentTraceStep, FinancialFact


def general_advisor_node(state: AgentState) -> Dict[str, Any]:
    """
    General Financial Advisor Agent:
    Handles general financial inquiries, cash flow planning, goal analysis, and health score consultations.
    """
    context = state.get("financial_context", {})
    query = state.get("query", "")
    intent = state.get("intent", "general_financial_question")
    
    system_prompt = (
        "You are the FinPilot Principal AI Financial Advisor. Your objective is to help the user navigate "
        "their personal finances, cash-flow allocation, goal planning, emergency runway, and financial health score. "
        "Provide structured, motivating, and mathematically sound guidance using only their verified financial data."
    )
    
    response_text = execute_llm_reasoning(
        prompt=query,
        system_prompt=system_prompt,
        intent=intent,
        context=context,
    )

    facts: List[FinancialFact] = []
    recommendations: List[AgentRecommendation] = []
    
    core = context.get("core_metrics", {})
    profile = context.get("profile", {})
    health = context.get("financial_health_score", {})
    cash_flow = context.get("cash_flow", {})
    goals = context.get("goals_portfolio", {})

    if health:
        facts.append({
            "metric": "Financial Health Score",
            "value": f"{health.get('overall_score', 0.0):.0f}/100",
            "category": "Health",
            "interpretation": f"Status: {health.get('status', 'healthy')}",
        })

    if core:
        facts.append({
            "metric": "Disposable Surplus",
            "value": f"${core.get('disposable_income', 0.0):,.2f}/mo",
            "category": "Cash Flow",
            "interpretation": f"Savings Rate: {core.get('savings_rate', 0.0):.1f}%",
        })
        facts.append({
            "metric": "Emergency Runway",
            "value": f"{core.get('emergency_fund_months', 0.0):.1f} mos",
            "category": "Safety",
            "interpretation": f"Target: 6.0 mos (${core.get('emergency_fund_target', 0.0):,.2f})",
        })

    if cash_flow:
        facts.append({
            "metric": "Safe-to-Spend Daily",
            "value": f"${cash_flow.get('safe_to_spend_daily', 0.0):,.2f}/day",
            "category": "Budgeting",
            "interpretation": f"{cash_flow.get('days_until_payday', 0)} days until next income cycle",
        })

    # Memory context integration
    memory_list = state.get("memory_context", [])
    if memory_list:
        for m in memory_list[:2]:
            item_lbl = m.get("item_name") or m.get("decision_type", "past decision")
            strat = m.get("strategy_selected") or "Evaluated"
            facts.append({
                "metric": f"Previous Decision: {item_lbl}",
                "value": strat,
                "category": "Decision Memory",
                "interpretation": f"Decision: {m.get('decision', '')[:60]}...",
            })

    # Actionable advice based on emergency fund & health
    if not core.get("is_emergency_fund_adequate", True):
        recommendations.append({
            "id": str(uuid.uuid4()),
            "type": "goal_acceleration",
            "title": "Build 3-6 Month Emergency Safety Net",
            "description": f"Your emergency fund currently covers {core.get('emergency_fund_months', 0.0):.1f} months. Prioritize allocating surplus until reaching ${core.get('emergency_fund_target', 0.0):,.2f}.",
            "potential_monthly_savings": None,
            "priority": "high",
            "category": "Emergency Fund",
        })

    if goals.get("has_conflicts"):
        recommendations.append({
            "id": str(uuid.uuid4()),
            "type": "budget_adjustment",
            "title": "Resolve Goal Allocation Shortfall",
            "description": f"Active goals require an extra ${goals.get('conflict_shortfall', 0.0):,.2f}/mo. Consider extending low-priority milestone dates.",
            "potential_monthly_savings": None,
            "priority": "medium",
            "category": "Goals",
        })

    trace_step: AgentTraceStep = {
        "step": "advisory_synthesis",
        "agent": "GeneralAdvisorAgent",
        "action": f"Synthesized advice for intent '{intent}'",
        "details": {
            "intent": intent,
            "facts_count": len(facts),
            "recommendations_count": len(recommendations),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    current_trace = list(state.get("execution_trace", []))
    current_trace.append(trace_step)

    return {
        "agent_response": response_text,
        "financial_facts": facts,
        "recommendations": recommendations,
        "execution_trace": current_trace,
    }
