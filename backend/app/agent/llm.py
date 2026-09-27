import json
import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger("finpilot.agent.llm")


def is_groq_available() -> bool:
    return bool(settings.GROQ_API_KEY and not settings.MOCK_LLM_MODE)


def get_llm():
    """Returns a LangChain ChatGroq instance if configured, or None for mock mode."""
    if is_groq_available():
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model_name=settings.GROQ_MODEL,
                temperature=0.2,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize ChatGroq ({e}), falling back to mock mode.")
            return None
    return None


def generate_mock_response(
    query: str,
    intent: str,
    context: Dict[str, Any],
) -> str:
    """
    Deterministic mock response generator for development and testing.
    Generates high quality, grounded reasoning directly using the pre-computed financial context facts.
    """
    profile = context.get("profile", {})
    core = context.get("core_metrics", {})
    expenses = context.get("expense_summary", {})
    categories = context.get("category_spending", [])
    unusual = context.get("unusual_spending_flags", [])
    intel = context.get("spending_intelligence", {})
    budgets = context.get("budget_performance", {})
    cash_flow = context.get("cash_flow", {})
    goals = context.get("goals_portfolio", {})
    health = context.get("financial_health_score", {})

    income = profile.get("monthly_income", 0.0)
    savings = profile.get("current_savings", 0.0)
    disposable = core.get("disposable_income", 0.0)
    savings_rate = core.get("savings_rate", 0.0)
    emergency_months = core.get("emergency_fund_months", 0.0)
    health_score = health.get("overall_score", 0.0)
    total_exp = expenses.get("total_expenses", 0.0)

    if intent == "spending_analysis":
        top_cats = sorted(categories, key=lambda x: x.get("total_amount", 0.0), reverse=True)[:3]
        top_cat_summary = ", ".join([f"**{c['category']}** (${c['total_amount']:,.2f}, {c['percentage_of_total']}%)" for c in top_cats]) if top_cats else "no recorded spending"
        
        flags_text = ""
        if unusual:
            flags_text = "\n\n⚠️ **Unusual Spending Detected:**\n" + "\n".join([f"- **{u['category']}**: Spent ${u['current_month_amount']:,.2f} (+{u['percentage_change']}% vs baseline) - {u['flag_reason']}" for u in unusual])
        
        misc = intel.get("miscellaneous_spending", {})
        misc_text = f" Miscellaneous leak is currently at **${misc.get('total_miscellaneous_amount', 0.0):,.2f}** ({misc.get('percentage_of_total_spend', 0.0)}% of total, risk: *{misc.get('leak_risk_level', 'low')}*)."

        return (
            f"### 📊 Spending Intelligence Analysis\n\n"
            f"Based on your transaction records, your total monthly spending is **${total_exp:,.2f}** "
            f"against a monthly income of **${income:,.2f}** (Savings Rate: **{savings_rate:.1f}%**).\n\n"
            f"**Top Spending Drivers:** {top_cat_summary}.{misc_text}"
            f"{flags_text}\n\n"
            f"**Key Takeaway:** Your discretionary spending makes up **{expenses.get('discretionary_ratio', 0.0):.1f}%** of your outflows. "
            f"Rebalancing discretionary categories will directly accelerate your savings growth."
        )

    elif intent == "expense_reduction":
        recurring = intel.get("recurring_expenses", [])
        hidden = intel.get("hidden_expenses", [])
        misc = intel.get("miscellaneous_spending", {})
        
        rec_list = []
        if hidden:
            for h in hidden[:2]:
                rec_list.append(f"- **{h['name']} ({h['category']})**: Leaking ~${h['monthly_leak']:,.2f}/mo (${h['annual_leak']:,.2f}/yr). *Tip: {h['optimization_tip']}*")
        if recurring:
            for r in recurring[:2]:
                rec_list.append(f"- **Recurring Subscription ({r['merchant']})**: ${r['estimated_amount']:,.2f} billed {r['frequency']}.")
        
        items_str = "\n".join(rec_list) if rec_list else "- Audit discretionary spending and miscellaneous transactions to free up cash."
        misc_leak = misc.get("total_miscellaneous_amount", 0.0)

        return (
            f"### 💡 Expense Reduction & Optimization Plan\n\n"
            f"We analyzed your recurring commitments and discretionary leaks to identify high-impact savings:\n\n"
            f"{items_str}\n\n"
            f"🔍 **Miscellaneous & Uncategorized Spending:**\n"
            f"You have **${misc_leak:,.2f}** in miscellaneous outlays. Capping this by 50% could recover **${(misc_leak * 0.5):,.2f}/month**.\n\n"
            f"**Recommended Action:** Consolidate subscriptions and establish dedicated category limits for non-essential purchases."
        )

    elif intent == "financial_plan" or intent == "cash_flow":
        safe_daily = cash_flow.get("safe_to_spend_daily", 0.0)
        days_left = cash_flow.get("days_until_payday", 0)
        survival_strict = cash_flow.get("survival_months_strict_essentials", 0.0)

        return (
            f"### 🧭 Cash-Flow & Financial Allocation Summary\n\n"
            f"- **Net Monthly Income:** ${income:,.2f}\n"
            f"- **Disposable Monthly Surplus:** ${disposable:,.2f}\n"
            f"- **Safe-to-Spend Daily Limit:** **${safe_daily:,.2f}/day** (with {days_left} days until next salary cycle)\n"
            f"- **Emergency Fund Runway:** **{emergency_months:.1f} months** (${profile.get('emergency_savings', 0.0):,.2f})\n"
            f"- **Income Shock Survival (Strict Essentials):** **{survival_strict:.1f} months**\n\n"
            f"Your overall Financial Health Score is **{health_score:.0f}/100** ({health.get('status', 'healthy')})."
        )

    elif intent == "goal_planning":
        active_goals = goals.get("goals", [])
        goals_text = ""
        if active_goals:
            goals_text = "\n".join([f"- **{g['name']}**: Saved ${g['current_amount']:,.2f} of ${g['target_amount']:,.2f} (Allocated: ${g['monthly_contribution']:,.2f}/mo, Required: ${g['required_monthly']:,.2f}/mo - {'✅ On Track' if g['is_on_track'] else '⚠️ Behind'})" for g in active_goals])
        else:
            goals_text = "- No active financial goals currently defined. You can create targets like Emergency Buffer, Home Down Payment, or Retirement."

        conflict_note = f"\n\n⚠️ **Goal Conflict Shortfall:** ${goals.get('conflict_shortfall', 0.0):,.2f}/month." if goals.get("has_conflicts") else "\n\n✅ Your current surplus covers your active goal contributions."

        return (
            f"### 🎯 Goal Strategy & Progress\n\n"
            f"You have **{goals.get('active_goals_count', 0)} active goals** totaling **${goals.get('total_target_amount', 0.0):,.2f}** in targets:\n\n"
            f"{goals_text}{conflict_note}\n\n"
            f"Available monthly surplus for goal funding: **${disposable:,.2f}/month**."
        )

    elif intent == "decision_evaluation":
        return (
            f"### ⚖️ Decision & Affordability Assessment\n\n"
            f"Evaluating your current financial foundation:\n"
            f"- **Monthly Surplus:** ${disposable:,.2f}\n"
            f"- **Liquid Savings:** ${savings:,.2f}\n"
            f"- **Debt-to-Income (DTI):** {core.get('debt_to_income_ratio', 0.0):.1f}%\n"
            f"- **Emergency Runway:** {emergency_months:.1f} months\n\n"
            f"To evaluate a specific purchase, loan, or income change, check the Scenario Planner to simulate immediate and long-term milestone impacts."
        )

    elif intent in ["monitoring_review", "monitoring"]:
        return (
            f"### 📡 Financial Monitoring Report\n\n"
            f"**Current Financial Health Score:** **{health_score:.0f}/100** ({health.get('status', 'healthy')})\n"
            f"- **Net Monthly Income:** ${income:,.2f}\n"
            f"- **Total Monthly Outflows:** ${total_exp:,.2f}\n"
            f"- **Disposable Surplus:** ${disposable:,.2f}/mo\n"
            f"- **Emergency Runway:** {emergency_months:.1f} months\n\n"
            f"**Diagnostic Summary:** Continuous monitoring is active. All baseline parameters, goal allocations, and recurring cash flows are being continuously evaluated."
        )

    elif intent in ["plan_adaptation", "replanning"]:
        return (
            f"### 🔄 Adaptive Financial Plan Proposal\n\n"
            f"We evaluated your updated financial state against existing plans:\n"
            f"- **Baseline Disposable Surplus:** ${disposable:,.2f}/mo\n"
            f"- **Health Status:** {health.get('status', 'healthy')} ({health_score:.0f}/100)\n\n"
            f"**Key Adaptation Options:**\n"
            f"1. **Balanced Recovery**: Trim discretionary expenses to preserve core target timelines.\n"
            f"2. **Goal Extension**: Maintain current lifestyle by extending lower-priority milestones.\n"
            f"3. **Aggressive Budget Cut**: Protect emergency liquidity with decisive expense caps.\n\n"
            f"Review the generated plan comparison table below to approve your preferred strategy."
        )

    elif intent == "memory_query":
        return (
            f"### 🧠 Decision Memory & Historical Review\n\n"
            f"Retrieved your previous decision records from persistent memory:\n"
            f"- **Current Disposable Surplus:** ${disposable:,.2f}/month\n"
            f"- **Current Safe-to-Spend:** ${cash_flow.get('safe_to_spend_daily', 0.0):,.2f}/day\n"
            f"- **Emergency Runway:** {emergency_months:.1f} months\n\n"
            f"**Circumstance Evaluation:** Your live financial parameters take priority over historical recommendations. "
            f"If your surplus or liquidity has changed, you can run a fresh scenario simulation to confirm affordability."
        )

    elif intent == "proactive_insights":
        return (
            f"### 💡 Proactive Financial Opportunities & Insights\n\n"
            f"Analyzing your live cash flows, goals, and decision memory:\n"
            f"- **Emergency Runway:** **{emergency_months:.1f} months** ({'✅ Healthy buffer' if emergency_months >= 3.0 else '⚠️ Needs reinforcement'})\n"
            f"- **Savings Rate:** **{savings_rate:.1f}%** of net income\n"
            f"- **Discretionary Outflow:** **{expenses.get('discretionary_ratio', 0.0):.1f}%** of total expenses\n\n"
            f"**Proactive Recommendation:** Review your Decision History to check if previous deferrals (such as delayed purchases or EMI plans) can now be safely re-evaluated."
        )

    else:
        return (
            f"### 🤖 FinPilot Financial Advisory\n\n"
            f"Based on your profile, your monthly income is **${income:,.2f}** with total essential expenses of **${profile.get('essential_expenses', 0.0):,.2f}** "
            f"and a monthly surplus of **${disposable:,.2f}**.\n\n"
            f"Your Financial Health Score is **{health_score:.0f}/100** ({health.get('status', 'healthy')}). "
            f"You can ask me to analyze your spending leaks, evaluate expense reduction opportunities, review goal timelines, or optimize your monthly budget allocation."
        )


def execute_llm_reasoning(
    prompt: str,
    system_prompt: str,
    intent: str,
    context: Dict[str, Any],
) -> str:
    """
    Executes reasoning via Groq LLM if configured, otherwise produces deterministic mock response.
    """
    llm = get_llm()
    if llm is not None:
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            context_summary = json.dumps(context, indent=2)
            full_system_prompt = (
                f"{system_prompt}\n\n"
                f"STRICT INSTRUCTIONS:\n"
                f"1. You are FinPilot AI's Financial Advisor.\n"
                f"2. Reason strictly over the verified financial facts provided in the context below.\n"
                f"3. NEVER fabricate or invent financial numbers, balances, or rates.\n"
                f"4. Format your response cleanly using GitHub markdown with headers, bold highlights, and bullet points.\n\n"
                f"VERIFIED FINANCIAL CONTEXT:\n```json\n{context_summary}\n```"
            )
            messages = [
                SystemMessage(content=full_system_prompt),
                HumanMessage(content=prompt),
            ]
            res = llm.invoke(messages)
            return str(res.content)
        except Exception as e:
            logger.warning(f"Groq invocation failed: {e}. Falling back to deterministic mock response.")
            return generate_mock_response(prompt, intent, context)
    
    return generate_mock_response(prompt, intent, context)
