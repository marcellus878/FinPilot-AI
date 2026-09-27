from datetime import datetime
from typing import Any, Dict, List
import uuid

from app.agent.llm import execute_llm_reasoning
from app.agent.state import AgentRecommendation, AgentState, AgentTraceStep, FinancialFact


def expense_reduction_node(state: AgentState) -> Dict[str, Any]:
    """
    Expense Reduction Agent:
    Identifies concrete, prioritized expense reduction and subscription optimization opportunities.
    """
    context = state.get("financial_context", {})
    query = state.get("query", "")
    
    system_prompt = (
        "You are the FinPilot Expense Reduction Agent. Your objective is to examine the user's recurring commitments, "
        "discretionary leaks, subscriptions, and high-spending categories to formulate actionable, high-impact "
        "cost-cutting strategies without sacrificing core essentials. Cite exact figures and potential savings."
    )
    
    response_text = execute_llm_reasoning(
        prompt=query,
        system_prompt=system_prompt,
        intent="expense_reduction",
        context=context,
    )

    facts: List[FinancialFact] = []
    recommendations: List[AgentRecommendation] = []
    
    intel = context.get("spending_intelligence", {})
    recurring = intel.get("recurring_expenses", [])
    hidden = intel.get("hidden_expenses", [])
    misc = intel.get("miscellaneous_spending", {})
    budgets = context.get("budget_performance", {})

    total_recurring = sum(r.get("estimated_amount", 0.0) for r in recurring)
    if total_recurring > 0:
        facts.append({
            "metric": "Recurring Commitments",
            "value": f"${total_recurring:,.2f}/mo",
            "category": "Recurring",
            "interpretation": f"{len(recurring)} detected recurring services/subscriptions",
        })

    if hidden:
        total_hidden = sum(h.get("monthly_leak", 0.0) for h in hidden)
        facts.append({
            "metric": "Hidden Leaks",
            "value": f"${total_hidden:,.2f}/mo",
            "category": "Optimization",
            "interpretation": f"${total_hidden * 12:,.2f} projected annual leakage",
        })

    # Recommendations from hidden expenses
    for h in hidden:
        recommendations.append({
            "id": str(uuid.uuid4()),
            "type": "expense_reduction",
            "title": f"Optimize {h['name']}",
            "description": f"{h['optimization_tip']} Potential annual savings: ${h['annual_leak']:,.2f}.",
            "potential_monthly_savings": round(h["monthly_leak"], 2),
            "priority": "high" if h["monthly_leak"] > 30 else "medium",
            "category": h["category"],
        })

    # Recommendations from recurring subscriptions
    for r in recurring:
        if r.get("category") in ["Entertainment", "Shopping", "Food & Dining"]:
            recommendations.append({
                "id": str(uuid.uuid4()),
                "type": "expense_reduction",
                "title": f"Review {r['merchant']} Subscription",
                "description": f"Evaluating or pausing {r['merchant']} ({r['frequency']}) could save ~${r['estimated_amount']:,.2f}/mo.",
                "potential_monthly_savings": round(r["estimated_amount"], 2),
                "priority": "medium",
                "category": r["category"],
            })

    # Recommendations from miscellaneous leaks
    if misc and misc.get("total_miscellaneous_amount", 0.0) > 0:
        misc_amt = misc["total_miscellaneous_amount"]
        recommendations.append({
            "id": str(uuid.uuid4()),
            "type": "expense_reduction",
            "title": "Trim Miscellaneous Spending",
            "description": f"Uncategorized/miscellaneous expenses total ${misc_amt:,.2f}. Capping this by 50% recovers ${misc_amt * 0.5:,.2f}/mo.",
            "potential_monthly_savings": round(misc_amt * 0.5, 2),
            "priority": "medium",
            "category": "Miscellaneous",
        })

    # Fallback discretionary optimization recommendation
    exp = context.get("expense_summary", {})
    if exp.get("discretionary_expenses", 0.0) > 0 and len(recommendations) == 0:
        disc_amt = exp["discretionary_expenses"]
        recommendations.append({
            "id": str(uuid.uuid4()),
            "type": "expense_reduction",
            "title": "Optimize Discretionary Spending",
            "description": f"Discretionary spending is ${disc_amt:,.2f} ({exp.get('discretionary_ratio', 0.0):.1f}% of total). Target a 15% reduction to save ${disc_amt * 0.15:,.2f}/mo.",
            "potential_monthly_savings": round(disc_amt * 0.15, 2),
            "priority": "medium",
            "category": "Discretionary",
        })

    trace_step: AgentTraceStep = {
        "step": "expense_reduction_analysis",
        "agent": "ExpenseReductionAgent",
        "action": "Generated targeted savings opportunities and cost-cutting recommendations",
        "details": {
            "facts_count": len(facts),
            "recommendations_count": len(recommendations),
            "total_potential_monthly_savings": sum(r["potential_monthly_savings"] or 0.0 for r in recommendations),
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
