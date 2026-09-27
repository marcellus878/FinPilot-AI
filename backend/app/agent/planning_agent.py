from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.agent.llm import execute_llm_reasoning
from app.agent.state import AgentRecommendation, AgentState, AgentTraceStep, FinancialFact
from app.financial_engine.goals import (
    GoalConflictStrategy,
    GoalPortfolioAnalysisResult,
    analyze_goal_portfolio,
    generate_goal_conflict_strategies,
)
from app.financial_engine.helpers import quantize_currency
from app.financial_engine.salary_planner import (
    SalaryAllocationResult,
    calculate_monthly_recurring_commitments,
    calculate_salary_allocation,
    calculate_salary_cycle_dates,
)

logger = logging.getLogger("finpilot.agent.planning")


def planning_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Planning Agent Node for LangGraph:
    Creates goal-oriented, cash-flow aware financial plans using deterministic calculations.
    Exposes goal conflict strategies (Waterfall, Proportional, Equal) transparently without inventing figures.
    """
    context = state.get("financial_context", {})
    query = state.get("query", "")
    current_trace = list(state.get("execution_trace", []))

    # Step 1: Trace Planning Request
    trace_request: AgentTraceStep = {
        "step": "planning_request",
        "agent": "PlanningAgent",
        "action": "Initiated goal and salary cash-flow planning analysis",
        "details": {"query": query},
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_request)

    profile = context.get("profile", {})
    core = context.get("core_metrics", {})
    goals_ctx = context.get("goals_portfolio", {})
    budget_perf = context.get("budget_performance", {})

    monthly_income = Decimal(str(profile.get("monthly_income", 5000.0)))
    disposable = Decimal(str(core.get("disposable_income", 2000.0)))
    current_savings = Decimal(str(profile.get("current_savings", 10000.0)))
    emergency_savings = Decimal(str(profile.get("emergency_savings", 5000.0)))

    # 1. Deterministic Salary Allocation
    total_budgeted_fixed = Decimal(str(budget_perf.get("total_budgeted", 1000.0)))
    salary_alloc: SalaryAllocationResult = calculate_salary_allocation(
        monthly_income=monthly_income,
        fixed_commitments=total_budgeted_fixed,
    )

    # 2. Deterministic Goals & Conflict Analysis
    goal_dicts = [
        {
            "id": g.get("id", f"goal_{i}"),
            "name": g.get("name", "Goal"),
            "target_amount": Decimal(str(g.get("target_amount", 0.0))),
            "current_amount": Decimal(str(g.get("current_amount", 0.0))),
            "monthly_contribution": Decimal(str(g.get("monthly_contribution", 0.0))),
            "target_date": g.get("target_date"),
            "priority": g.get("priority", "medium"),
            "status": "in_progress",
        }
        for i, g in enumerate(goals_ctx.get("goals", []))
    ]

    goal_portfolio: GoalPortfolioAnalysisResult = analyze_goal_portfolio(
        goals=goal_dicts,
        available_monthly_capacity=disposable,
    )

    # Step 2: Trace Analysis Started
    trace_analysis_start: AgentTraceStep = {
        "step": "planning_analysis_started",
        "agent": "PlanningAgent",
        "action": f"Evaluated {goal_portfolio.active_goals_count} goals. Conflict detected: {goal_portfolio.conflict_detected}",
        "details": {
            "total_monthly_required": str(goal_portfolio.total_required_monthly),
            "available_capacity": str(goal_portfolio.available_monthly_capacity),
            "has_conflicts": goal_portfolio.conflict_detected,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_analysis_start)

    # 3. Generate Goal Conflict Strategies if conflicts detected
    conflict_strategies: List[GoalConflictStrategy] = []
    if goal_portfolio.conflict_detected or len(goal_dicts) > 1:
        conflict_strategies = generate_goal_conflict_strategies(
            goals=[
                {
                    "id": g["id"],
                    "name": g["name"],
                    "priority": g["priority"],
                    "target_amount": g["target_amount"],
                    "current_amount": g["current_amount"],
                    "required_monthly": g["target_amount"] / Decimal("12.00") if g.get("target_amount") else Decimal("100.00"),
                    "status": "in_progress",
                }
                for g in goal_dicts
            ],
            available_monthly_funds=disposable,
        )

    # 4. Synthesize AI Advisory Response
    system_prompt = (
        "You are the FinPilot Planning Agent. Your objective is to design transparent, goal-oriented "
        "financial plans. Address salary allocation, emergency fund safety, goal timelines, and explain "
        "competing goal resolution options (Waterfall, Proportional, Equal Split). Ground all figures in the verified facts."
    )

    reasoning_prompt = (
        f"User Planning Question: {query}\n\n"
        f"Verified Financial Context:\n"
        f"- Monthly Income: ${monthly_income:,.2f}\n"
        f"- Available Monthly Capacity / Surplus: ${disposable:,.2f}\n"
        f"- Active Goals Count: {goal_portfolio.active_goals_count}\n"
        f"- Total Goal Funding Required: ${goal_portfolio.total_required_monthly:,.2f}/mo\n"
        f"- Conflict Status: {'Conflict Detected (Shortfall $' + str(abs(goal_portfolio.net_monthly_surplus_or_shortfall)) + '/mo)' if goal_portfolio.conflict_detected else 'Fully Funded Within Surplus'}\n"
        f"- Salary Allocation: Fixed ${salary_alloc.fixed_commitments:,.2f}, Essentials ${salary_alloc.essential_allowance:,.2f}, Savings Target ${salary_alloc.savings_target:,.2f}, Discretionary ${salary_alloc.discretionary_allowance:,.2f}, Safety Buffer ${salary_alloc.remaining_buffer:,.2f}"
    )

    agent_response_text = execute_llm_reasoning(
        prompt=reasoning_prompt,
        system_prompt=system_prompt,
        intent="financial_plan",
        context=context,
    )

    # Fallback to rich markdown if LLM returned generic template
    if "Cash-Flow & Financial Allocation Summary" in agent_response_text or "Goal Strategy" in agent_response_text:
        conflict_section = ""
        if goal_portfolio.conflict_detected and conflict_strategies:
            conflict_section = (
                f"\n\n### ⚖️ Competing Goal Strategies\n"
                f"Your active goals require **${goal_portfolio.total_required_monthly:,.2f}/mo**, exceeding your available monthly surplus of **${disposable:,.2f}** by **${abs(goal_portfolio.net_monthly_surplus_or_shortfall):,.2f}**.\n\n"
                f"Choose an allocation strategy:\n"
                f"1. **Priority Waterfall:** Fully funds high-priority targets first, then cascades remaining surplus to secondary milestones.\n"
                f"2. **Proportional Progress:** Funds all goals simultaneously in proportion to their target amount.\n"
                f"3. **Equal Split:** Distributes available monthly surplus equally across all goals (${(disposable / max(1, len(goal_dicts))):,.2f} each)."
            )

        agent_response_text = (
            f"### 🧭 Structured Financial Plan & Salary Allocation\n\n"
            f"Based on your net monthly income of **${monthly_income:,.2f}** and available monthly surplus of **${disposable:,.2f}**:\n\n"
            f"**Recommended Monthly Allocation:**\n"
            f"- **Fixed & Recurring Commitments:** ${salary_alloc.fixed_commitments:,.2f} ({salary_alloc.fixed_percentage}%)\n"
            f"- **Essential Living Allowance:** ${salary_alloc.essential_allowance:,.2f} ({salary_alloc.essential_percentage}%)\n"
            f"- **Savings & Goals Allocation:** ${salary_alloc.savings_target:,.2f} ({salary_alloc.savings_percentage}%)\n"
            f"- **Discretionary Spending Allowance:** ${salary_alloc.discretionary_allowance:,.2f} ({salary_alloc.discretionary_percentage}%)\n"
            f"- **Safety Buffer:** ${salary_alloc.remaining_buffer:,.2f} ({salary_alloc.buffer_percentage}%)\n\n"
            f"**Goal Portfolio Status:**\n"
            f"- **Active Goals:** {goal_portfolio.active_goals_count} goals totaling ${goal_portfolio.total_target_amount:,.2f} in target funds\n"
            f"- **Portfolio Feasibility:** {'✅ Fully Feasible' if goal_portfolio.is_portfolio_feasible else '⚠️ Requires Rebalancing'}"
            f"{conflict_section}\n\n"
            f"**Actionable Advice:** {salary_alloc.explanation}"
        )

    # Compile structured FinancialFacts
    financial_facts: List[FinancialFact] = [
        {
            "metric": "Monthly Savings Target",
            "value": f"${salary_alloc.savings_target:,.2f}/mo",
            "category": "Allocation",
            "interpretation": f"{salary_alloc.savings_percentage}% of monthly income",
        },
        {
            "metric": "Available Goal Capacity",
            "value": f"${disposable:,.2f}/mo",
            "category": "Cash Flow",
            "interpretation": f"Required: ${goal_portfolio.total_required_monthly:,.2f}/mo",
        },
        {
            "metric": "Discretionary Budget Cap",
            "value": f"${salary_alloc.discretionary_allowance:,.2f}/mo",
            "category": "Budgeting",
            "interpretation": f"{salary_alloc.discretionary_percentage}% allowance",
        },
        {
            "metric": "Unallocated Safety Buffer",
            "value": f"${salary_alloc.remaining_buffer:,.2f}/mo",
            "category": "Safety",
            "interpretation": f"{salary_alloc.buffer_percentage}% cushion",
        },
    ]

    # Compile Recommendations & Strategy Options
    recommendations: List[AgentRecommendation] = []
    
    if goal_portfolio.conflict_detected and conflict_strategies:
        for strat in conflict_strategies:
            recommendations.append({
                "id": str(uuid.uuid4()),
                "type": "goal_strategy",
                "title": f"Strategy: {strat.strategy_name}",
                "description": strat.description,
                "potential_monthly_savings": None,
                "priority": "high" if strat.strategy_id == "priority_waterfall" else "medium",
                "category": "Goal Strategy",
            })
    else:
        recommendations.append({
            "id": str(uuid.uuid4()),
            "type": "salary_allocation",
            "title": "Automate Monthly Salary Allocation",
            "description": f"Transfer ${salary_alloc.savings_target:,.2f} directly to savings on payday to maintain consistent {salary_alloc.savings_percentage}% savings discipline.",
            "potential_monthly_savings": float(salary_alloc.savings_target),
            "priority": "high",
            "category": "Planning",
        })

    trace_complete: AgentTraceStep = {
        "step": "planning_analysis_completed",
        "agent": "PlanningAgent",
        "action": "Generated goal-aware allocation plan and conflict strategies",
        "details": {
            "strategies_count": len(conflict_strategies),
            "is_portfolio_feasible": goal_portfolio.is_portfolio_feasible,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_complete)

    return {
        "agent_response": agent_response_text,
        "financial_facts": financial_facts,
        "recommendations": recommendations,
        "execution_trace": current_trace,
    }
