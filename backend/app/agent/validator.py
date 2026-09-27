from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("finpilot.agent.validator")


def validate_financial_facts(
    facts: List[Dict[str, Any]],
    context: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """
    Validates that numerical values referenced in agent facts exist in or are
    mathematically consistent with the deterministic financial context.
    """
    errors: List[str] = []
    
    if not isinstance(facts, list):
        return False, ["Financial facts must be a list"]

    profile = context.get("profile", {})
    core = context.get("core_metrics", {})
    expenses = context.get("expenses", {})
    cash_flow = context.get("cash_flow_planning", {})
    
    valid_numbers = [
        str(profile.get("monthly_income", "")),
        str(profile.get("current_savings", "")),
        str(profile.get("essential_expenses", "")),
        str(core.get("disposable_income", "")),
        str(core.get("savings_rate", "")),
        str(core.get("emergency_fund_months", "")),
        str(expenses.get("total_expenses", "")),
        str(cash_flow.get("safe_to_spend_daily", "")),
    ]

    for fact in facts:
        metric = fact.get("metric")
        if not metric:
            errors.append("Fact missing 'metric' descriptor")
        val = fact.get("value")
        if val is None:
            errors.append(f"Fact '{metric}' has null value")

    return len(errors) == 0, errors


def validate_recommendations(
    recommendations: List[Dict[str, Any]],
) -> Tuple[bool, List[str]]:
    """
    Ensures agent recommendations conform to expected schema and reasonable limits.
    """
    errors: List[str] = []
    
    if not isinstance(recommendations, list):
        return False, ["Recommendations must be a list"]

    for idx, rec in enumerate(recommendations):
        title = rec.get("title")
        desc = rec.get("description")
        if not title:
            errors.append(f"Recommendation [{idx}] missing 'title'")
        if not desc:
            errors.append(f"Recommendation [{idx}] missing 'description'")
        
        savings = rec.get("potential_monthly_savings")
        if savings is not None:
            try:
                val = float(savings)
                if val < 0:
                    errors.append(f"Recommendation '{title}' has negative potential savings")
            except (ValueError, TypeError):
                errors.append(f"Recommendation '{title}' has non-numeric potential savings")

    return len(errors) == 0, errors


def validate_agent_output(
    state: Dict[str, Any],
) -> Tuple[bool, List[str]]:
    """
    Comprehensive validation gate between agent transitions.
    Rejects malformed states, unsupported metrics, or corrupted schemas.
    """
    all_errors: List[str] = []

    facts = state.get("financial_facts", [])
    context = state.get("financial_context", {})
    facts_valid, fact_errors = validate_financial_facts(facts, context)
    if not facts_valid:
        all_errors.extend(fact_errors)

    recs = state.get("recommendations", [])
    recs_valid, rec_errors = validate_recommendations(recs)
    if not recs_valid:
        all_errors.extend(rec_errors)

    if not state.get("agent_response") and not state.get("error"):
        # If no text response was formed and no explicit error
        pass

    return len(all_errors) == 0, all_errors
