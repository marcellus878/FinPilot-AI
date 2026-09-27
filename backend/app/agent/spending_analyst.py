from datetime import datetime
from typing import Any, Dict, List
import uuid

from app.agent.llm import execute_llm_reasoning
from app.agent.state import AgentRecommendation, AgentState, AgentTraceStep, FinancialFact


def spending_analyst_node(state: AgentState) -> Dict[str, Any]:
    """
    Spending Analyst Agent:
    Evaluates spending patterns, unusual increases, and discretionary leaks.
    Grounds all commentary strictly in verified facts.
    """
    context = state.get("financial_context", {})
    query = state.get("query", "")
    
    system_prompt = (
        "You are the FinPilot Spending Analyst Agent. Your objective is to examine the user's spending "
        "history, category breakdown, unusual spending spikes, discretionary ratio, and miscellaneous leaks. "
        "Highlight key insights clearly and explain where their money is going without speculating."
    )
    
    response_text = execute_llm_reasoning(
        prompt=query,
        system_prompt=system_prompt,
        intent="spending_analysis",
        context=context,
    )

    # Compile structured financial facts for the UI
    facts: List[FinancialFact] = []
    exp = context.get("expense_summary", {})
    if exp:
        facts.append({
            "metric": "Total Spending",
            "value": f"${exp.get('total_expenses', 0.0):,.2f}",
            "category": "Expenses",
            "interpretation": f"{exp.get('transaction_count', 0)} recorded transactions",
        })
        facts.append({
            "metric": "Discretionary Ratio",
            "value": f"{exp.get('discretionary_ratio', 0.0):.1f}%",
            "category": "Discretionary",
            "interpretation": f"${exp.get('discretionary_expenses', 0.0):,.2f} spent on non-essentials",
        })

    intel = context.get("spending_intelligence", {})
    misc = intel.get("miscellaneous_spending", {})
    if misc and misc.get("total_miscellaneous_amount", 0.0) > 0:
        facts.append({
            "metric": "Miscellaneous Leaks",
            "value": f"${misc.get('total_miscellaneous_amount', 0.0):,.2f}",
            "category": "Leaks",
            "interpretation": f"Risk level: {misc.get('leak_risk_level', 'low')}",
        })

    unusual = context.get("unusual_spending_flags", [])
    if unusual:
        top_flag = unusual[0]
        facts.append({
            "metric": f"Spike: {top_flag['category']}",
            "value": f"+{top_flag['percentage_change']}%",
            "category": "Alert",
            "interpretation": f"${top_flag['current_month_amount']:,.2f} vs avg ${top_flag['baseline_average']:,.2f}",
        })

    # Generate actionable recommendation objects
    recommendations: List[AgentRecommendation] = []
    if misc and misc.get("total_miscellaneous_amount", 0.0) > 50:
        recommendations.append({
            "id": str(uuid.uuid4()),
            "type": "expense_reduction",
            "title": "Plug Miscellaneous Spending Leak",
            "description": f"Cap unclassified outlays. Cutting miscellaneous spending by half saves ~${misc['total_miscellaneous_amount'] * 0.5:,.2f}/mo.",
            "potential_monthly_savings": round(misc["total_miscellaneous_amount"] * 0.5, 2),
            "priority": "high" if misc.get("leak_risk_level") == "high" else "medium",
            "category": "Miscellaneous",
        })

    if unusual:
        for u in unusual[:2]:
            recommendations.append({
                "id": str(uuid.uuid4()),
                "type": "budget_adjustment",
                "title": f"Review Surge in {u['category']}",
                "description": f"Spending in {u['category']} rose by {u['percentage_change']}% above baseline. Set a category budget limit to prevent drift.",
                "potential_monthly_savings": max(0.0, round(u["current_month_amount"] - u["baseline_average"], 2)),
                "priority": "medium",
                "category": u["category"],
            })

    trace_step: AgentTraceStep = {
        "step": "spending_analysis",
        "agent": "SpendingAnalystAgent",
        "action": "Analyzed spending breakdown and compiled facts & recommendations",
        "details": {
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
