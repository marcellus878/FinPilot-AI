from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.agent.llm import execute_llm_reasoning
from app.agent.monitoring_agent import (
    build_current_live_snapshot,
    extract_or_build_baseline_snapshot,
)
from app.agent.state import AgentRecommendation, AgentState, AgentTraceStep, FinancialFact
from app.financial_engine.monitoring import (
    PlanComparisonTable,
    ReplanningStrategyOption,
    generate_adaptive_replanning_strategies,
    generate_plan_comparison,
)

logger = logging.getLogger("finpilot.agent.replanning")


def replanning_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Adaptive Replanning Agent Node:
    1. Evaluates monitoring triggers.
    2. Runs deterministic strategy and plan comparison generators.
    3. Formulates multi-strategy alternatives without mutating database records.
    4. Logs lifecycle events and outputs structured plan comparison and advice.
    """
    context = state.get("financial_context", {})
    query = state.get("query", "")
    current_trace = list(state.get("execution_trace", []))

    baseline = extract_or_build_baseline_snapshot(context)
    current = build_current_live_snapshot(context)
    goals_list = context.get("goals_portfolio", {}).get("goals", [])

    # Step 1: Replanning Started
    current_trace.append({
        "step": "replanning_started",
        "agent": "ReplanningAgent",
        "action": "Generating deterministic adaptive plan alternatives",
        "details": {"query": query},
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Step 2: Generate Strategies
    strategies: List[ReplanningStrategyOption] = generate_adaptive_replanning_strategies(
        current=current,
        baseline=baseline,
        active_goals=goals_list,
    )
    current_trace.append({
        "step": "revised_plan_generated",
        "agent": "ReplanningAgent",
        "action": f"Generated {len(strategies)} adaptive planning alternatives",
        "details": {
            "strategies_count": len(strategies),
            "strategy_titles": [s.title for s in strategies],
        },
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Step 3: Before / After Plan Comparison (using primary balanced strategy)
    primary_strategy = strategies[0] if strategies else ReplanningStrategyOption(
        strategy_id="fallback",
        title="Default Allocation",
        description="Standard allocation",
        adjusted_essential=current.monthly_essential_expenses,
        adjusted_savings=Decimal("1000.00"),
        adjusted_discretionary=Decimal("500.00"),
        resulting_buffer=Decimal("200.00"),
        impact_on_goals="Nominal",
    )

    assessment_reasons = state.get("replanning_assessment", {}).get("reasons", ["Financial adjustments required"])
    plan_comp: PlanComparisonTable = generate_plan_comparison(
        baseline=baseline,
        proposed_strategy=primary_strategy,
        reason="; ".join(assessment_reasons),
        active_goals=goals_list,
    )

    current_trace.append({
        "step": "plan_comparison_generated",
        "agent": "ReplanningAgent",
        "action": f"Compiled side-by-side transition matrix across {len(plan_comp.items)} metrics",
        "details": {
            "comparison_metrics": [i.metric for i in plan_comp.items],
            "affected_goals_count": len(plan_comp.affected_goals),
        },
        "timestamp": datetime.utcnow().isoformat(),
    })

    current_trace.append({
        "step": "monitoring_completed",
        "agent": "ReplanningAgent",
        "action": "Finished adaptive replanning evaluation with non-destructive plan proposal",
        "details": {"status": "completed"},
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Step 4: Compile Facts & Recommendations
    financial_facts: List[FinancialFact] = list(state.get("financial_facts", []))
    financial_facts.extend([
        {
            "metric": "Proposed Monthly Savings",
            "value": f"${primary_strategy.adjusted_savings:,.2f}/mo",
            "category": "Replanning",
            "interpretation": primary_strategy.title,
        },
        {
            "metric": "Proposed Discretionary Cap",
            "value": f"${primary_strategy.adjusted_discretionary:,.2f}/mo",
            "category": "Replanning",
            "interpretation": f"Safe Daily: ${quantize_safe:,.2f}/day" if (quantize_safe := primary_strategy.adjusted_discretionary / Decimal("30")) else "",
        },
        {
            "metric": "Safety Buffer",
            "value": f"${primary_strategy.resulting_buffer:,.2f}/mo",
            "category": "Replanning",
            "interpretation": "Unallocated Cash Reserve",
        },
    ])

    recommendations: List[AgentRecommendation] = list(state.get("recommendations", []))
    for s in strategies:
        recommendations.append({
            "id": str(uuid.uuid4()),
            "type": "plan_adaptation_strategy",
            "title": s.title,
            "description": f"{s.description} — {s.impact_on_goals}",
            "potential_monthly_savings": None,
            "priority": "medium",
            "category": "Proposed Strategy",
        })

    # Step 5: Synthesize markdown response
    system_prompt = (
        "You are the FinPilot Adaptive Replanning Agent. Present the revised proposed plan, explain why "
        "rebalancing was calculated, show the before vs. after impact on savings, daily spend, and goals, "
        "and outline the alternative strategies."
    )
    reasoning_prompt = (
        f"User Query: {query}\n\n"
        f"Adaptive Plan Comparison:\n"
        f"- Primary Proposal: {primary_strategy.title}\n"
        f"- Description: {primary_strategy.description}\n"
        f"- Essential Allowance: ${primary_strategy.adjusted_essential:,.2f}\n"
        f"- Savings Allocation: ${primary_strategy.adjusted_savings:,.2f}\n"
        f"- Discretionary Spending: ${primary_strategy.adjusted_discretionary:,.2f}\n"
        f"- Resulting Buffer: ${primary_strategy.resulting_buffer:,.2f}\n"
        f"- Goal Impact: {primary_strategy.impact_on_goals}\n\n"
        f"Available Alternatives:\n" + "\n".join([f"• {s.title}: {s.description}" for s in strategies])
    )

    agent_response_text = execute_llm_reasoning(
        prompt=reasoning_prompt,
        system_prompt=system_prompt,
        intent="plan_adaptation",
        context=context,
    )

    if "Adaptive Financial Plan & Replanning Proposal" in agent_response_text or len(agent_response_text) < 100:
        agent_response_text = (
            f"### 🔄 Adaptive Financial Plan Proposal\n\n"
            f"Based on recent monitored financial changes, FinPilot has generated an updated plan proposal:\n\n"
            f"**Recommended Strategy:** `{primary_strategy.title}`\n"
            f"{primary_strategy.description}\n\n"
            f"**Before vs. Proposed Plan Comparison:**\n"
            f"- **Savings & Goals Allocation:** ${baseline.monthly_income - baseline.monthly_essential_expenses - baseline.monthly_discretionary_expenses:,.2f}/mo → **${primary_strategy.adjusted_savings:,.2f}/mo**\n"
            f"- **Discretionary Spending:** ${baseline.monthly_discretionary_expenses:,.2f}/mo → **${primary_strategy.adjusted_discretionary:,.2f}/mo**\n"
            f"- **Unallocated Buffer:** $0.00/mo → **${primary_strategy.resulting_buffer:,.2f}/mo**\n"
            f"- **Goal Impact:** {primary_strategy.impact_on_goals}\n\n"
            f"**Available Strategic Options:**\n"
            + "\n".join([f"- **{s.title}:** {s.description}" for s in strategies]) + "\n\n"
            f"*Note: Existing plan records remain active until you explicitly apply a proposed adaptation.*"
        )

    # Convert comparison and strategies to dicts
    comp_dict = {
        "items": [
            {
                "area": it.area,
                "metric": it.metric,
                "baseline_value": it.baseline_value,
                "proposed_value": it.proposed_value,
                "delta": it.delta,
                "explanation": it.explanation,
            }
            for it in plan_comp.items
        ],
        "summary": plan_comp.summary,
        "affected_goals": plan_comp.affected_goals,
    }

    strategies_dicts = [
        {
            "strategy_id": s.strategy_id,
            "title": s.title,
            "description": s.description,
            "adjusted_essential": str(s.adjusted_essential),
            "adjusted_savings": str(s.adjusted_savings),
            "adjusted_discretionary": str(s.adjusted_discretionary),
            "resulting_buffer": str(s.resulting_buffer),
            "impact_on_goals": s.impact_on_goals,
            "tradeoffs": s.tradeoffs,
        }
        for s in strategies
    ]

    return {
        "agent_response": agent_response_text,
        "financial_facts": financial_facts,
        "recommendations": recommendations,
        "execution_trace": current_trace,
        "plan_comparison": comp_dict,
        "replanning_strategies": strategies_dicts,
    }
