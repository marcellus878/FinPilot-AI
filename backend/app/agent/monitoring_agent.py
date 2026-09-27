from datetime import datetime
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid

from app.agent.llm import execute_llm_reasoning
from app.agent.state import AgentRecommendation, AgentState, AgentTraceStep, FinancialFact
from app.financial_engine.monitoring import (
    FinancialChangeItem,
    MonitoringSnapshot,
    ReplanningAssessment,
    build_monitoring_snapshot,
    detect_financial_changes,
    evaluate_replanning_triggers,
)

logger = logging.getLogger("finpilot.agent.monitoring")


def extract_or_build_baseline_snapshot(context: Dict[str, Any]) -> MonitoringSnapshot:
    """Extracts previously saved baseline snapshot or builds default from profile."""
    plan = context.get("salary_plan", {})
    sal_prof = plan.get("salary_profile", {})
    stored_baseline = sal_prof.get("monitoring_baseline") or plan.get("monitoring_baseline")

    profile = context.get("profile", {})
    income = Decimal(str(profile.get("monthly_income", 5000.0)))
    essential = Decimal(str(profile.get("essential_expenses", 2500.0)))
    debt = Decimal(str(profile.get("monthly_debt_payment", 0.0)))
    savings = Decimal(str(profile.get("current_savings", 10000.0)))

    if stored_baseline and isinstance(stored_baseline, dict):
        return build_monitoring_snapshot(
            monthly_income=stored_baseline.get("monthly_income", income),
            essential_expenses=stored_baseline.get("monthly_essential_expenses", essential),
            discretionary_expenses=stored_baseline.get("monthly_discretionary_expenses", income * Decimal("0.15")),
            current_savings=stored_baseline.get("current_savings", savings),
            monthly_debt=stored_baseline.get("monthly_debt_payment", debt),
            safe_to_spend_daily=stored_baseline.get("safe_to_spend_daily", Decimal("25.00")),
            emergency_runway_months=stored_baseline.get("emergency_runway_months", Decimal("4.0")),
            emergency_runway_status=stored_baseline.get("emergency_runway_status", "adequate"),
            financial_health_score=stored_baseline.get("financial_health_score", Decimal("80.0")),
            financial_health_grade=stored_baseline.get("financial_health_grade", "A"),
            budget_variance=stored_baseline.get("budget_variance", Decimal("0.00")),
            recurring_commitments_monthly=stored_baseline.get("recurring_commitments_monthly", Decimal("500.00")),
            active_goals_count=int(stored_baseline.get("active_goals_count", 1)),
            goals_monthly_required=stored_baseline.get("goals_monthly_required", Decimal("500.00")),
            goals_monthly_capacity=stored_baseline.get("goals_monthly_capacity", Decimal("1000.00")),
            goals_feasible=bool(stored_baseline.get("goals_feasible", True)),
        )

    # Standard baseline synthesis if no previous snapshot stored
    discretionary = max(Decimal("0.00"), income * Decimal("0.15"))
    safe_daily = quantize_safe = max(Decimal("0.00"), (income - essential - debt) * Decimal("0.50") / Decimal("30.00"))
    runway = (savings / essential) if essential > 0 else Decimal("6.0")

    return build_monitoring_snapshot(
        monthly_income=income,
        essential_expenses=essential,
        discretionary_expenses=discretionary,
        current_savings=savings,
        monthly_debt=debt,
        safe_to_spend_daily=quantize_safe,
        emergency_runway_months=runway,
        emergency_runway_status="adequate" if runway >= 3 else "vulnerable",
        financial_health_score=Decimal("80.00"),
        financial_health_grade="A",
        budget_variance=Decimal("0.00"),
        recurring_commitments_monthly=Decimal("500.00"),
        active_goals_count=len(context.get("goals_portfolio", {}).get("goals", [])),
        goals_monthly_required=Decimal(str(context.get("goals_portfolio", {}).get("total_required_monthly", 500.0))),
        goals_monthly_capacity=Decimal(str(context.get("goals_portfolio", {}).get("available_monthly_capacity", 1000.0))),
        goals_feasible=bool(context.get("goals_portfolio", {}).get("is_portfolio_feasible", True)),
    )


def build_current_live_snapshot(context: Dict[str, Any]) -> MonitoringSnapshot:
    """Builds live current monitoring snapshot from context."""
    profile = context.get("profile", {})
    expense_sum = context.get("expense_summary", {})
    safe_spend = context.get("safe_to_spend", {})
    health = context.get("financial_health_score", {})
    budgets = context.get("budget_performance", {})
    goals_port = context.get("goals_portfolio", {})
    plan = context.get("salary_plan", {})

    income = Decimal(str(profile.get("monthly_income", 5000.0)))
    essential = Decimal(str(expense_sum.get("essential_spending", profile.get("essential_expenses", 2500.0))))
    discretionary = Decimal(str(expense_sum.get("non_essential_spending", 750.0)))
    savings = Decimal(str(profile.get("current_savings", 10000.0)))
    debt = Decimal(str(profile.get("monthly_debt_payment", 0.0)))

    safe_daily = Decimal(str(safe_spend.get("daily_safe_to_spend", 25.0)))
    runway_months = Decimal(str(profile.get("indicators", {}).get("emergency_fund", {}).get("months_covered", 4.0)))
    runway_status = str(profile.get("indicators", {}).get("emergency_fund", {}).get("status_label", "adequate"))
    health_score = Decimal(str(health.get("overall_score", 78.0)))
    health_grade = str(health.get("grade", "B"))

    variance = Decimal(str(budgets.get("overall_variance", 0.0)))
    recurring_items = plan.get("recurring_commitments", [])
    recurring_total = Decimal("0.00")
    for r in recurring_items:
        recurring_total += Decimal(str(r.get("monthly_equivalent", r.get("amount", 0.0))))

    active_goals = goals_port.get("goals", [])
    goals_req = Decimal(str(goals_port.get("total_required_monthly", 0.0)))
    goals_cap = Decimal(str(goals_port.get("available_monthly_capacity", max(0, float(income - essential - debt)))))
    goals_feasible = bool(goals_port.get("is_portfolio_feasible", True))

    return build_monitoring_snapshot(
        monthly_income=income,
        essential_expenses=essential,
        discretionary_expenses=discretionary,
        current_savings=savings,
        monthly_debt=debt,
        safe_to_spend_daily=safe_daily,
        emergency_runway_months=runway_months,
        emergency_runway_status=runway_status,
        financial_health_score=health_score,
        financial_health_grade=health_grade,
        budget_variance=variance,
        recurring_commitments_monthly=recurring_total,
        active_goals_count=len(active_goals),
        goals_monthly_required=goals_req,
        goals_monthly_capacity=goals_cap,
        goals_feasible=goals_feasible,
    )


def monitoring_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Monitoring Agent Node:
    1. Loads baseline and live current state.
    2. Runs deterministic change detection.
    3. Evaluates replanning triggers.
    4. Logs lifecycle traces.
    5. Returns updated state.
    """
    context = state.get("financial_context", {})
    query = state.get("query", "")
    current_trace = list(state.get("execution_trace", []))

    # Step 1: Monitoring Started
    current_trace.append({
        "step": "monitoring_started",
        "agent": "MonitoringAgent",
        "action": "Initiated financial state monitoring and change detection",
        "details": {"query": query},
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Step 2: Baseline Loaded & Current State Built
    baseline = extract_or_build_baseline_snapshot(context)
    current_trace.append({
        "step": "baseline_loaded",
        "agent": "MonitoringAgent",
        "action": f"Retrieved baseline financial plan (Income: ${baseline.monthly_income:,.2f})",
        "details": {
            "baseline_income": str(baseline.monthly_income),
            "baseline_essential": str(baseline.monthly_essential_expenses),
            "baseline_savings": str(baseline.current_savings),
        },
        "timestamp": datetime.utcnow().isoformat(),
    })

    current = build_current_live_snapshot(context)
    current_trace.append({
        "step": "current_state_built",
        "agent": "MonitoringAgent",
        "action": f"Constructed live financial snapshot (Health: {current.financial_health_score}/100)",
        "details": {
            "current_income": str(current.monthly_income),
            "current_essential": str(current.monthly_essential_expenses),
            "current_discretionary": str(current.monthly_discretionary_expenses),
            "current_safe_to_spend": str(current.safe_to_spend_daily),
        },
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Step 3: Change Detection
    changes: List[FinancialChangeItem] = detect_financial_changes(baseline, current)
    current_trace.append({
        "step": "financial_changes_detected",
        "agent": "MonitoringAgent",
        "action": f"Detected {len(changes)} meaningful financial changes against baseline",
        "details": {
            "changes_count": len(changes),
            "critical_count": len([c for c in changes if c.severity == "critical"]),
            "high_count": len([c for c in changes if c.severity == "high"]),
            "metrics": [c.metric for c in changes],
        },
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Step 4: Replanning Assessment
    assessment: ReplanningAssessment = evaluate_replanning_triggers(changes, current, baseline)
    current_trace.append({
        "step": "replanning_assessment_started",
        "agent": "MonitoringAgent",
        "action": f"Evaluated deterministic replanning trigger rules (Verdict: {'Required' if assessment.replanning_required else 'Not Required'})",
        "details": {
            "replanning_required": assessment.replanning_required,
            "trigger": assessment.trigger,
            "severity": assessment.severity,
            "affected_areas": assessment.affected_areas,
        },
        "timestamp": datetime.utcnow().isoformat(),
    })

    if assessment.replanning_required:
        current_trace.append({
            "step": "replanning_required",
            "agent": "MonitoringAgent",
            "action": f"Replanning triggered due to {assessment.trigger.replace('_', ' ')}",
            "details": {"reasons": assessment.reasons},
            "timestamp": datetime.utcnow().isoformat(),
        })
    else:
        current_trace.append({
            "step": "replanning_not_required",
            "agent": "MonitoringAgent",
            "action": "Plan remains on track; no structural adjustments needed",
            "details": {"reasons": assessment.reasons},
            "timestamp": datetime.utcnow().isoformat(),
        })

    # Step 5: Format Facts and Markdown Response
    financial_facts: List[FinancialFact] = [
        {
            "metric": "Plan Status",
            "value": "Replanning Required" if assessment.replanning_required else "On Track",
            "category": "Monitoring",
            "interpretation": f"Primary Trigger: {assessment.trigger.replace('_', ' ').title()}",
        },
        {
            "metric": "Changes Detected",
            "value": f"{len(changes)} Metrics",
            "category": "Monitoring",
            "interpretation": f"Critical: {len([c for c in changes if c.severity == 'critical'])}, High: {len([c for c in changes if c.severity == 'high'])}",
        },
        {
            "metric": "Emergency Runway",
            "value": f"{current.emergency_runway_months} mos",
            "category": "Safety",
            "interpretation": f"Status: {current.emergency_runway_status}",
        },
        {
            "metric": "Daily Safe-to-Spend",
            "value": f"${current.safe_to_spend_daily}/day",
            "category": "Cash Flow",
            "interpretation": f"Baseline: ${baseline.safe_to_spend_daily}/day",
        },
    ]

    # Recommendations
    recommendations: List[AgentRecommendation] = []
    for r in assessment.recommendations:
        recommendations.append({
            "id": str(uuid.uuid4()),
            "type": "monitoring_action",
            "title": "Monitoring Recommendation",
            "description": r,
            "potential_monthly_savings": None,
            "priority": assessment.severity if assessment.replanning_required else "low",
            "category": "Plan Adaptation",
        })

    # System & Reasoning Prompts
    system_prompt = (
        "You are the FinPilot Financial Monitoring Agent. Your responsibility is to explain what changes occurred "
        "in the user's financial life and whether their active plan requires adaptation. Present verified facts, "
        "mathematical differences, and affected financial pillars without inventing figures."
    )
    reasoning_prompt = (
        f"User Query: {query}\n\n"
        f"Monitoring Snapshot & Change Results:\n"
        f"- Replanning Required: {assessment.replanning_required} (Trigger: {assessment.trigger}, Severity: {assessment.severity})\n"
        f"- Affected Areas: {', '.join(assessment.affected_areas) if assessment.affected_areas else 'None'}\n"
        f"- Key Reasons:\n" + "\n".join([f"  • {r}" for r in assessment.reasons]) + "\n\n"
        f"- Detected Changes:\n" + "\n".join([f"  • {c.description} (Severity: {c.severity})" for c in changes])
    )

    agent_response_text = execute_llm_reasoning(
        prompt=reasoning_prompt,
        system_prompt=system_prompt,
        intent="monitoring_review",
        context=context,
    )

    if "Financial Plan Monitoring & Change Detection" in agent_response_text or len(agent_response_text) < 100:
        status_emoji = "⚠️" if assessment.replanning_required else "✅"
        status_text = "Plan Requires Adaptation" if assessment.replanning_required else "Plan On Track"
        agent_response_text = (
            f"### {status_emoji} Financial Monitoring Report: {status_text}\n\n"
            f"**Plan Status:** `{status_text.upper()}` (Severity: `{assessment.severity.upper()}`)\n\n"
            f"**Key Monitored Observations:**\n"
            + "\n".join([f"- {r}" for r in assessment.reasons]) + "\n\n"
            f"**Detected Financial Changes:**\n"
            + ("\n".join([f"- **{c.metric.replace('_', ' ').title()}:** {c.description}" for c in changes]) if changes else "- No significant deviations from baseline plan detected.\n") + "\n\n"
            f"**Recommended Action:**\n"
            + "\n".join([f"- {rec}" for rec in assessment.recommendations])
        )

    # Convert Snapshot & Changes to Dicts for LangGraph State
    changes_dicts = [
        {
            "metric": c.metric,
            "baseline": str(c.baseline),
            "current": str(c.current),
            "absolute_change": str(c.absolute_change),
            "percentage_change": str(c.percentage_change),
            "severity": c.severity,
            "source": c.source,
            "description": c.description,
        }
        for c in changes
    ]

    snapshot_dict = {
        "monthly_income": str(current.monthly_income),
        "monthly_essential_expenses": str(current.monthly_essential_expenses),
        "monthly_discretionary_expenses": str(current.monthly_discretionary_expenses),
        "monthly_total_expenses": str(current.monthly_total_expenses),
        "current_savings": str(current.current_savings),
        "monthly_debt_payment": str(current.monthly_debt_payment),
        "savings_rate": str(current.savings_rate),
        "safe_to_spend_daily": str(current.safe_to_spend_daily),
        "emergency_runway_months": str(current.emergency_runway_months),
        "emergency_runway_status": current.emergency_runway_status,
        "financial_health_score": str(current.financial_health_score),
        "financial_health_grade": current.financial_health_grade,
        "budget_variance": str(current.budget_variance),
        "recurring_commitments_monthly": str(current.recurring_commitments_monthly),
        "active_goals_count": current.active_goals_count,
        "goals_monthly_required": str(current.goals_monthly_required),
        "goals_monthly_capacity": str(current.goals_monthly_capacity),
        "goals_feasible": current.goals_feasible,
        "timestamp": current.timestamp.isoformat(),
    }

    assessment_dict = {
        "replanning_required": assessment.replanning_required,
        "trigger": assessment.trigger,
        "severity": assessment.severity,
        "affected_areas": assessment.affected_areas,
        "reasons": assessment.reasons,
        "recommendations": assessment.recommendations,
    }

    return {
        "agent_response": agent_response_text,
        "financial_facts": financial_facts,
        "recommendations": recommendations,
        "execution_trace": current_trace,
        "monitoring_snapshot": snapshot_dict,
        "financial_changes": changes_dicts,
        "replanning_assessment": assessment_dict,
    }
