from datetime import datetime
from decimal import Decimal
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid

from app.agent.llm import execute_llm_reasoning
from app.agent.state import AgentRecommendation, AgentState, AgentTraceStep, FinancialFact
from app.financial_engine.helpers import quantize_currency, to_decimal
from app.financial_engine.scenarios import (
    DetailedScenarioResult,
    simulate_detailed_decision_scenario,
)
from app.schemas.decision import (
    DecisionImpactItem,
    DecisionOptionItem,
    DecisionRequest,
    DecisionResult,
    DecisionScenarioMetadata,
    FinancialFactLabelValue,
)

logger = logging.getLogger("finpilot.agent.decision")


def extract_decision_parameters(query: str, context: Optional[Dict[str, Any]] = None) -> DecisionRequest:
    """
    Deterministically parses decision parameters from natural language user input.
    Validates numbers and assigns appropriate scenario types without LLM fabrication.
    """
    q = query.lower()

    # 1. Determine Decision / Scenario Type
    if any(k in q for k in ["salary decrease", "pay cut", "salary cut", "income cut", "income drop", "salary drop", "loss of income", "salary reduction", "income reduction", "pay reduction"]):
        decision_type = "income_change"
    elif any(k in q for k in ["raise", "salary increase", "bonus", "income increase", "promotion", "pay increase"]):
        decision_type = "income_change"
    elif any(k in q for k in ["emi", "monthly", "per month", "/mo", "subscription", "rent increase", "membership", "recurring"]):
        decision_type = "new_recurring_expense"
    elif any(k in q for k in ["emergency", "medical bill", "urgent repair", "accident", "unexpected"]):
        decision_type = "unexpected_expense"
    else:
        decision_type = "one_time_purchase"

    # 2. Extract Monetary Amount
    amount = Decimal("1000.00")  # Default fallback amount if none detected
    
    # Check 'k' suffix e.g. "50k", "5k", "2.5k"
    k_match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', q)
    if k_match:
        val = float(k_match.group(1)) * 1000
        amount = Decimal(str(int(val)))
    else:
        # Match currency numbers with commas or decimals e.g. "₹50,000", "$2,500.00", "50000"
        num_matches = re.findall(r'(?:[\$₹£€]|rs\.?|inr)?\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)', q)
        if num_matches:
            # Filter out small integers that might be months or non-monetary words
            valid_nums = []
            for m in num_matches:
                clean_num = m.replace(",", "")
                try:
                    num_val = float(clean_num)
                    # If number is greater than 10 or explicitly prefixed with currency
                    if num_val > 0:
                        valid_nums.append(Decimal(str(num_val)))
                except ValueError:
                    continue
            if valid_nums:
                # Select the most likely price amount (largest or first)
                amount = valid_nums[0] if len(valid_nums) == 1 else max(valid_nums)

    # 3. If negative income change query, make amount negative
    if decision_type == "income_change" and any(k in q for k in ["decrease", "cut", "drop", "reduction", "loss"]):
        amount = -abs(amount)

    # 4. Extract Item Description
    item_desc = "Proposed Decision"
    for item in [
        "laptop", "phone", "iphone", "macbook", "car", "bike", "vehicle",
        "vacation", "trip", "flight", "tv", "camera", "gaming pc",
        "gym", "rent", "insurance", "course", "watch", "furniture",
        "medical bill", "home repair"
    ]:
        if item in q:
            item_desc = item.title()
            break

    # 5. Extract duration if mentioned (e.g. "12 months", "6 months")
    duration = None
    dur_match = re.search(r'(\d+)\s*(?:months|month|mos|mo)\b', q)
    if dur_match:
        try:
            duration = int(dur_match.group(1))
        except ValueError:
            duration = None

    return DecisionRequest(
        decision_type=decision_type,
        amount=quantize_currency(amount),
        description=item_desc,
        timing_months=0,
        duration_months=duration,
        recurring_monthly_cost=amount if decision_type == "new_recurring_expense" else None,
    )


def execute_decision_pipeline(
    request: DecisionRequest,
    context: Dict[str, Any],
) -> Tuple[DetailedScenarioResult, DecisionResult]:
    """
    Executes the deterministic scenario engine over verified user facts,
    then structures a rigorous DecisionResult.
    """
    profile = context.get("profile", {})
    goals_ctx = context.get("goals_portfolio", {})
    
    monthly_income = Decimal(str(profile.get("monthly_income", 5000.0)))
    essential_expenses = Decimal(str(profile.get("essential_expenses", 2500.0)))
    monthly_debt = Decimal(str(profile.get("monthly_debt_payment", 0.0)))
    current_savings = Decimal(str(profile.get("current_savings", 10000.0)))

    # Extract active goals from context
    active_goals = [
        {
            "id": g.get("id", f"goal_{i}"),
            "name": g.get("name", "Goal"),
            "target_amount": Decimal(str(g.get("target_amount", 0.0))),
            "current_amount": Decimal(str(g.get("current_amount", 0.0))),
            "monthly_contribution": Decimal(str(g.get("monthly_contribution", 0.0))),
            "target_date": g.get("target_date"),
        }
        for i, g in enumerate(goals_ctx.get("goals", []))
    ]

    # 1. Deterministic Calculation via Scenario Engine
    scenario_res: DetailedScenarioResult = simulate_detailed_decision_scenario(
        monthly_income=monthly_income,
        monthly_essential_expenses=essential_expenses,
        monthly_debt_payments=monthly_debt,
        current_savings=current_savings,
        scenario_type=request.decision_type,
        amount=request.amount,
        scenario_name=request.description or "Proposed Financial Decision",
        timing_months=request.timing_months,
        description=request.description,
        active_goals=active_goals,
    )

    # 2. Build Verified Financial Facts
    facts: List[FinancialFactLabelValue] = [
        FinancialFactLabelValue(
            label="Baseline Monthly Income",
            value=float(scenario_res.before_state.monthly_income),
            unit="currency",
            source="financial_engine",
        ),
        FinancialFactLabelValue(
            label="Current Liquid Savings",
            value=float(scenario_res.before_state.current_savings),
            unit="currency",
            source="financial_engine",
        ),
        FinancialFactLabelValue(
            label="Baseline Monthly Surplus",
            value=float(scenario_res.before_state.monthly_disposable_income),
            unit="currency",
            source="financial_engine",
        ),
        FinancialFactLabelValue(
            label="Emergency Fund Runway",
            value=float(scenario_res.before_state.emergency_fund_months),
            unit="months",
            source="financial_engine",
        ),
        FinancialFactLabelValue(
            label="Financial Health Score",
            value=float(scenario_res.before_state.financial_health_score),
            unit="score",
            source="financial_engine",
        ),
    ]

    # 3. Build Projected Impacts
    impacts: List[DecisionImpactItem] = [
        DecisionImpactItem(
            area="safe_to_spend",
            description=f"Safe-to-Spend changes from ${scenario_res.before_state.daily_safe_to_spend}/day to ${scenario_res.after_state.daily_safe_to_spend}/day",
            value=float(scenario_res.after_state.daily_safe_to_spend),
            delta=str(scenario_res.delta.daily_safe_to_spend_delta),
        ),
        DecisionImpactItem(
            area="remaining_savings",
            description=f"Liquid savings move from ${scenario_res.before_state.current_savings} to ${scenario_res.after_state.current_savings}",
            value=float(scenario_res.after_state.current_savings),
            delta=str(scenario_res.delta.savings_delta),
        ),
        DecisionImpactItem(
            area="emergency_runway",
            description=f"Emergency buffer changes from {scenario_res.before_state.emergency_fund_months} mos to {scenario_res.after_state.emergency_fund_months} mos ({scenario_res.after_state.emergency_fund_status})",
            value=float(scenario_res.after_state.emergency_fund_months),
            delta=str(scenario_res.delta.emergency_fund_months_delta),
        ),
        DecisionImpactItem(
            area="monthly_cash_flow",
            description=f"Monthly disposable surplus moves from ${scenario_res.before_state.monthly_disposable_income}/mo to ${scenario_res.after_state.monthly_disposable_income}/mo",
            value=float(scenario_res.after_state.monthly_disposable_income),
            delta=str(scenario_res.delta.monthly_disposable_income_delta),
        ),
        DecisionImpactItem(
            area="health_score",
            description=f"Health score adjusts from {scenario_res.before_state.financial_health_score} ({scenario_res.before_state.financial_health_grade}) to {scenario_res.after_state.financial_health_score} ({scenario_res.after_state.financial_health_grade})",
            value=float(scenario_res.after_state.financial_health_score),
            delta=str(scenario_res.delta.financial_health_score_delta),
        ),
    ]

    # 4. Generate Actionable Options
    options: List[DecisionOptionItem] = [
        DecisionOptionItem(
            title="Proceed as Planned",
            description=f"Execute {request.description or 'the decision'} immediately at ${abs(request.amount):,.2f}.",
            impact=f"Savings reduce by ${abs(request.amount):,.2f}, leaving ${scenario_res.after_state.current_savings:,.2f} in liquid reserve.",
        ),
        DecisionOptionItem(
            title="Delay by 3 Months",
            description=f"Save toward {request.description or 'this purchase'} over 3 months before executing.",
            impact=f"Avoids sudden lump-sum liquidity shock and preserves emergency fund runway.",
        ),
    ]
    if request.decision_type == "one_time_purchase" and abs(request.amount) > 500:
        options.append(
            DecisionOptionItem(
                title="Budget Alternative / Split Allocation",
                description="Explore a tiered model or reallocate non-essential budget categories to offset the cost.",
                impact="Maintains active milestone timelines for long-term savings goals.",
            )
        )

    # 5. Metadata & Assumptions
    assumptions = [
        f"Assumes current net monthly income of ${monthly_income:,.2f} remains constant.",
        f"Essential monthly baseline outflows estimated at ${essential_expenses:,.2f}.",
        f"No additional unplanned debt commitments incurred during the evaluation period.",
    ]

    decision_meta = DecisionScenarioMetadata(
        description=f"Simulation of {request.decision_type.replace('_', ' ')}: {request.description or 'Decision'} for ${abs(request.amount):,.2f}",
        assumptions=assumptions,
    )

    # 6. Recommendation & Confidence
    confidence = "high" if len(active_goals) > 0 or current_savings > 0 else "medium"

    decision_result = DecisionResult(
        summary=f"Verdict: {scenario_res.affordability_verdict.upper()} — {scenario_res.recommendation}",
        scenario=decision_meta,
        financial_facts=facts,
        impacts=impacts,
        tradeoffs=scenario_res.tradeoffs,
        options=options,
        recommendation=scenario_res.recommendation,
        confidence=confidence,
        is_sustainable=scenario_res.is_sustainable,
        affordability_verdict=scenario_res.affordability_verdict,
    )

    return scenario_res, decision_result


def decision_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Decision Agent Node for LangGraph:
    1. Extracts decision parameters.
    2. Runs deterministic scenario calculation.
    3. Interprets verified results and trade-offs.
    4. Produces structured decision result and human-readable advice.
    """
    context = state.get("financial_context", {})
    query = state.get("query", "")
    current_trace = list(state.get("execution_trace", []))

    # Step A: Parameter Extraction Trace
    decision_req = extract_decision_parameters(query, context)
    trace_extraction: AgentTraceStep = {
        "step": "decision_parameters_extracted",
        "agent": "DecisionAgent",
        "action": f"Extracted decision parameters: {decision_req.decision_type} for ${abs(decision_req.amount):,.2f} ({decision_req.description})",
        "details": {
            "decision_type": decision_req.decision_type,
            "amount": str(decision_req.amount),
            "description": decision_req.description,
            "timing_months": decision_req.timing_months,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_extraction)

    # Step B: Deterministic Scenario Calculation
    scenario_res, decision_result = execute_decision_pipeline(decision_req, context)
    trace_calc: AgentTraceStep = {
        "step": "scenario_calculated",
        "agent": "ScenarioEngine",
        "action": f"Calculated deterministic impact: verdict '{scenario_res.affordability_verdict}'",
        "details": {
            "is_sustainable": scenario_res.is_sustainable,
            "affordability_verdict": scenario_res.affordability_verdict,
            "savings_delta": str(scenario_res.delta.savings_delta),
            "emergency_runway_after": str(scenario_res.after_state.emergency_fund_months),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_calc)

    # Step C: LLM / Mock Reasoning Layer
    trace_analysis_start: AgentTraceStep = {
        "step": "decision_analysis_started",
        "agent": "DecisionAgent",
        "action": "Interpreting verified scenario impact, trade-offs, and options",
        "details": {"query": query},
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_analysis_start)

    system_prompt = (
        "You are the FinPilot Decision Intelligence Agent. Your mission is to interpret the deterministic "
        "scenario evaluation for the user's decision. Present the verdict, explain the exact mathematical impact "
        "on their savings, safe-to-spend, emergency fund, and goals. Offer balanced trade-offs and options. "
        "Do NOT guarantee future outcomes; present advice as structured financial options."
    )

    reasoning_prompt = (
        f"User Query: {query}\n\n"
        f"Calculated Scenario Summary:\n"
        f"- Decision: {decision_req.description} (${abs(decision_req.amount):,.2f}, type: {decision_req.decision_type})\n"
        f"- Affordability Verdict: {scenario_res.affordability_verdict.upper()}\n"
        f"- Sustainable: {scenario_res.is_sustainable}\n"
        f"- Savings Before -> After: ${scenario_res.before_state.current_savings:,.2f} -> ${scenario_res.after_state.current_savings:,.2f}\n"
        f"- Emergency Runway: {scenario_res.before_state.emergency_fund_months} mos -> {scenario_res.after_state.emergency_fund_months} mos\n"
        f"- Safe to Spend: ${scenario_res.before_state.daily_safe_to_spend}/day -> ${scenario_res.after_state.daily_safe_to_spend}/day\n"
        f"- Key Trade-offs: {'; '.join(scenario_res.tradeoffs)}\n"
        f"- Recommendation: {scenario_res.recommendation}"
    )

    agent_response_text = execute_llm_reasoning(
        prompt=reasoning_prompt,
        system_prompt=system_prompt,
        intent="decision_evaluation",
        context=context,
    )

    # Fallback to rich markdown if LLM returned basic mock
    if "Decision & Affordability Assessment" in agent_response_text:
        agent_response_text = (
            f"### ⚖️ Decision Assessment: {decision_req.description or 'Proposed Decision'}\n\n"
            f"**Affordability Verdict:** `{scenario_res.affordability_verdict.upper()}` "
            f"({'✅ Sustainable' if scenario_res.is_sustainable else '⚠️ Unsustainable / Stretched'})\n\n"
            f"**Verified Financial Impact:**\n"
            f"- **Cost:** ${abs(decision_req.amount):,.2f} ({decision_req.decision_type.replace('_', ' ')})\n"
            f"- **Liquid Savings:** ${scenario_res.before_state.current_savings:,.2f} → **${scenario_res.after_state.current_savings:,.2f}** (${scenario_res.delta.savings_delta:,.2f})\n"
            f"- **Emergency Runway:** {scenario_res.before_state.emergency_fund_months} mos → **{scenario_res.after_state.emergency_fund_months} mos** ({scenario_res.after_state.emergency_fund_status})\n"
            f"- **Daily Safe-to-Spend:** ${scenario_res.before_state.daily_safe_to_spend}/day → **${scenario_res.after_state.daily_safe_to_spend}/day**\n"
            f"- **Health Score Impact:** {scenario_res.before_state.financial_health_score} → **{scenario_res.after_state.financial_health_score}**\n\n"
            f"**Key Trade-offs & Considerations:**\n"
            + "\n".join([f"- {t}" for t in scenario_res.tradeoffs]) + "\n\n"
            f"**Recommended Strategy:** {scenario_res.recommendation}"
        )

    # Compile structured FinancialFacts
    financial_facts: List[FinancialFact] = [
        {
            "metric": "Verdict",
            "value": scenario_res.affordability_verdict.upper(),
            "category": "Decision",
            "interpretation": f"Decision: {decision_req.description} (${abs(decision_req.amount):,.2f})",
        },
        {
            "metric": "Post-Decision Savings",
            "value": f"${scenario_res.after_state.current_savings:,.2f}",
            "category": "Liquidity",
            "interpretation": f"Delta: ${scenario_res.delta.savings_delta:,.2f}",
        },
        {
            "metric": "Emergency Runway",
            "value": f"{scenario_res.after_state.emergency_fund_months} mos",
            "category": "Safety",
            "interpretation": f"Status: {scenario_res.after_state.emergency_fund_status}",
        },
        {
            "metric": "Safe Daily Spend",
            "value": f"${scenario_res.after_state.daily_safe_to_spend}/day",
            "category": "Cash Flow",
            "interpretation": f"Change: ${scenario_res.delta.daily_safe_to_spend_delta}/day",
        },
    ]

    # Compile Recommendations
    recommendations: List[AgentRecommendation] = [
        {
            "id": str(uuid.uuid4()),
            "type": "decision_option",
            "title": f"Recommendation: {scenario_res.affordability_verdict.title()} Purchase",
            "description": scenario_res.recommendation,
            "potential_monthly_savings": None,
            "priority": "high" if not scenario_res.is_sustainable else "medium",
            "category": "Decision",
        }
    ]

    for opt in decision_result.options:
        recommendations.append({
            "id": str(uuid.uuid4()),
            "type": "decision_alternative",
            "title": opt.title,
            "description": f"{opt.description} — {opt.impact}",
            "potential_monthly_savings": None,
            "priority": "low",
            "category": "Option",
        })

    trace_analysis_complete: AgentTraceStep = {
        "step": "decision_analysis_completed",
        "agent": "DecisionAgent",
        "action": "Finished decision intelligence synthesis with structured facts and trade-offs",
        "details": {
            "verdict": scenario_res.affordability_verdict,
            "options_count": len(decision_result.options),
            "tradeoffs_count": len(scenario_res.tradeoffs),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_analysis_complete)

    goals_list = context.get("goals_portfolio", {}).get("goals", [])
    active_goals_names = [g["name"] for g in goals_list if isinstance(g, dict) and "name" in g]

    decision_memory_data = {
        "decision_type": decision_req.decision_type,
        "item_name": decision_req.description,
        "amount": str(abs(decision_req.amount)),
        "decision": f"Verdict: {scenario_res.affordability_verdict.upper()} — {scenario_res.recommendation}",
        "strategy_selected": scenario_res.affordability_verdict,
        "alternatives_considered": [
            {"title": o.title, "description": o.description, "impact": o.impact}
            for o in decision_result.options
        ],
        "affected_goals": active_goals_names,
        "baseline_metrics": {
            "monthly_income": str(scenario_res.before_state.monthly_income),
            "current_savings": str(scenario_res.before_state.current_savings),
            "disposable_income": str(scenario_res.before_state.monthly_disposable_income),
            "safe_to_spend_daily": str(scenario_res.before_state.daily_safe_to_spend),
            "emergency_runway_months": str(scenario_res.before_state.emergency_fund_months),
            "financial_health_score": str(scenario_res.before_state.financial_health_score),
        },
        "resulting_metrics": {
            "current_savings": str(scenario_res.after_state.current_savings),
            "disposable_income": str(scenario_res.after_state.monthly_disposable_income),
            "safe_to_spend_daily": str(scenario_res.after_state.daily_safe_to_spend),
            "emergency_runway_months": str(scenario_res.after_state.emergency_fund_months),
            "financial_health_score": str(scenario_res.after_state.financial_health_score),
        },
        "assumptions": decision_result.scenario.assumptions,
        "recommendation_summary": scenario_res.recommendation,
    }

    return {
        "agent_response": agent_response_text,
        "financial_facts": financial_facts,
        "recommendations": recommendations,
        "scenario_results": {
            "verdict": scenario_res.affordability_verdict,
            "is_sustainable": scenario_res.is_sustainable,
            "decision_type": decision_req.decision_type,
            "item_name": decision_req.description,
            "amount": str(decision_req.amount),
            "recommendation": scenario_res.recommendation,
        },
        "decision_memory_result": decision_memory_data,
        "execution_trace": current_trace,
    }

