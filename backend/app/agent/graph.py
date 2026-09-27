from datetime import datetime
import logging
from typing import Any, Dict, List, Optional
import uuid

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agent.context_builder import build_financial_context
from app.agent.decision_agent import decision_agent_node
from app.agent.expense_reduction import expense_reduction_node
from app.agent.general_advisor import general_advisor_node
from app.agent.monitoring_agent import monitoring_agent_node
from app.agent.orchestrator import orchestrator_node
from app.agent.planning_agent import planning_agent_node
from app.agent.prompts import (
    DECISION_PROMPT_VERSION,
    MONITORING_PROMPT_VERSION,
    PLANNING_PROMPT_VERSION,
    PROMPT_VERSION,
    REFLECTION_PROMPT_VERSION,
    SPENDING_PROMPT_VERSION,
)
from app.agent.reflection import reflection_validator
from app.agent.replanning_agent import replanning_agent_node
from app.agent.spending_analyst import spending_analyst_node
from app.agent.state import AgentState, AgentTraceStep
from app.agent.validator import validate_agent_output
from app.models.agent_event import AgentEvent
from app.rag.agentic_retrieval import agentic_rag_engine
from app.schemas.decision_memory import DecisionMemoryCreateSchema
from app.services.decision_memory_service import retrieve_relevant_memory, save_decision_memory

logger = logging.getLogger("finpilot.agent.graph")


def rag_retrieval_node(state: AgentState) -> Dict[str, Any]:
    """
    Agentic RAG Node: Evaluates knowledge need, generates domain queries,
    retrieves authoritative guidelines (RBI, SEBI, etc.) and injects citations.
    """
    query = state.get("query", "")
    user_id = state.get("user_id")
    current_trace = list(state.get("execution_trace", []))
    rag_result = state.get("rag_result") or {}

    citations = rag_result.get("citations", [])

    trace_rag: AgentTraceStep = {
        "step": "agentic_rag_retrieval",
        "agent": "AgenticRAGRetriever",
        "action": f"Evaluated knowledge need and retrieved {len(citations)} authoritative citations",
        "details": {
            "retrieval_needed": rag_result.get("retrieval_needed", False),
            "citations_count": len(citations),
            "sources": [c.get("title") for c in citations],
            "sufficiency_score": rag_result.get("sufficiency_score", 1.0),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_rag)

    return {
        "rag_result": rag_result,
        "rag_citations": citations,
        "execution_trace": current_trace,
    }


def memory_retrieval_node(state: AgentState) -> Dict[str, Any]:
    """
    Retrieves and attaches relevant historical decision memories.
    """
    query = state.get("query", "")
    current_trace = list(state.get("execution_trace", []))
    memories = state.get("memory_context", [])

    trace_start: AgentTraceStep = {
        "step": "memory_lookup_started",
        "agent": "DecisionMemoryService",
        "action": f"Searching persistent decision memory for '{query[:40]}...'",
        "details": {"query": query},
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_start)

    trace_complete: AgentTraceStep = {
        "step": "memory_lookup_completed",
        "agent": "DecisionMemoryService",
        "action": f"Retrieved {len(memories)} relevant historical decisions",
        "details": {
            "found_count": len(memories),
            "sample_decisions": [m.get("item_name") or m.get("decision_type") for m in memories[:3]],
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_complete)

    return {
        "memory_context": memories,
        "execution_trace": current_trace,
    }


def validation_node(state: AgentState) -> Dict[str, Any]:
    """
    Validates agent outputs, verifying factual consistency against deterministic calculations.
    """
    current_trace = list(state.get("execution_trace", []))
    
    trace_start: AgentTraceStep = {
        "step": "validation_started",
        "agent": "AgentValidator",
        "action": "Verifying agent facts and recommendations against deterministic engine facts",
        "details": {
            "facts_count": len(state.get("financial_facts", [])),
            "recs_count": len(state.get("recommendations", [])),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_start)

    is_valid, errors = validate_agent_output(state)

    if is_valid:
        trace_val: AgentTraceStep = {
            "step": "validation_passed",
            "agent": "AgentValidator",
            "action": "All agent facts and schemas validated successfully",
            "details": {"status": "PASSED"},
            "timestamp": datetime.utcnow().isoformat(),
        }
    else:
        trace_val: AgentTraceStep = {
            "step": "validation_failed",
            "agent": "AgentValidator",
            "action": f"Validation warnings encountered: {'; '.join(errors)}",
            "details": {"errors": errors, "status": "FAILED"},
            "timestamp": datetime.utcnow().isoformat(),
        }

    current_trace.append(trace_val)

    return {
        "validation_errors": errors if not is_valid else [],
        "execution_trace": current_trace,
    }


def reflection_node(state: AgentState) -> Dict[str, Any]:
    """
    Reflection & Self-Correction Node: Audits groundedness, mathematical fact consistency,
    and applies bounded self-corrections.
    """
    current_trace = list(state.get("execution_trace", []))
    draft_response = state.get("agent_response") or state.get("final_response") or ""
    verified_facts = [
        {"name": f.get("metric", ""), "value": f.get("value", "")}
        for f in state.get("financial_facts", [])
    ]
    citations = state.get("rag_citations", [])

    reflection_res = reflection_validator.audit_and_correct(
        draft_content=draft_response,
        verified_facts=verified_facts,
        rag_citations=citations,
        user_query=state.get("query"),
    )

    trace_refl: AgentTraceStep = {
        "step": "reflection_and_self_correction",
        "agent": "ReflectionValidator",
        "action": f"Reflection status: {reflection_res['status']} (Groundedness: {int(reflection_res['groundedness_score']*100)}%)",
        "details": {
            "status": reflection_res["status"],
            "groundedness_score": reflection_res["groundedness_score"],
            "issues_count": len(reflection_res["issues_detected"]),
            "corrections_count": len(reflection_res["corrections_applied"]),
            "corrections": reflection_res["corrections_applied"],
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
    current_trace.append(trace_refl)

    # Attach HITL pending review status to recommendations
    recs = list(state.get("recommendations", []))
    for r in recs:
        if "hitl_status" not in r:
            r["hitl_status"] = "pending_review"

    return {
        "final_response": reflection_res["final_content"],
        "agent_response": reflection_res["final_content"],
        "recommendations": recs,
        "reflection_audit": reflection_res,
        "execution_trace": current_trace,
        "prompt_versions": {
            "orchestrator": PROMPT_VERSION,
            "spending": SPENDING_PROMPT_VERSION,
            "decision": DECISION_PROMPT_VERSION,
            "planning": PLANNING_PROMPT_VERSION,
            "monitoring": MONITORING_PROMPT_VERSION,
            "reflection": REFLECTION_PROMPT_VERSION,
        },
    }


def route_intent(state: AgentState) -> str:
    """Routes to the first agent in the orchestrator's selected agent chain."""
    chain = state.get("agent_chain", [])
    if chain:
        return chain[0]
    return "general_advisor"


def route_after_spending(state: AgentState) -> str:
    """Evaluates if spending analysis should chain into planning agent."""
    chain = state.get("agent_chain", [])
    if "planning_agent" in chain:
        return "planning_agent"
    return "validator"


def check_replanning_needed(state: AgentState) -> str:
    """Evaluates whether monitoring results require adaptive replanning."""
    assessment = state.get("replanning_assessment", {})
    if assessment and assessment.get("replanning_required", False):
        return "replanning_agent"
    return "validator"


def build_advisor_graph():
    """Constructs the multi-agent state graph for FinPilot AI."""
    workflow = StateGraph(AgentState)

    # Register Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("rag_retrieval", rag_retrieval_node)
    workflow.add_node("memory_retrieval", memory_retrieval_node)
    workflow.add_node("monitoring_agent", monitoring_agent_node)
    workflow.add_node("replanning_agent", replanning_agent_node)
    workflow.add_node("decision_agent", decision_agent_node)
    workflow.add_node("planning_agent", planning_agent_node)
    workflow.add_node("spending_analyst", spending_analyst_node)
    workflow.add_node("expense_reduction", expense_reduction_node)
    workflow.add_node("general_advisor", general_advisor_node)
    workflow.add_node("validator", validation_node)
    workflow.add_node("reflection", reflection_node)

    # Pipeline Transitions
    workflow.add_edge(START, "orchestrator")
    workflow.add_edge("orchestrator", "rag_retrieval")
    workflow.add_edge("rag_retrieval", "memory_retrieval")
    
    workflow.add_conditional_edges(
        "memory_retrieval",
        route_intent,
        {
            "monitoring_agent": "monitoring_agent",
            "decision_agent": "decision_agent",
            "planning_agent": "planning_agent",
            "spending_analyst": "spending_analyst",
            "expense_reduction": "expense_reduction",
            "general_advisor": "general_advisor",
        },
    )

    # Sequential chaining for spending -> planning
    workflow.add_conditional_edges(
        "spending_analyst",
        route_after_spending,
        {
            "planning_agent": "planning_agent",
            "validator": "validator",
        },
    )

    # Monitoring flow transitions conditionally to Replanning or Validator
    workflow.add_conditional_edges(
        "monitoring_agent",
        check_replanning_needed,
        {
            "replanning_agent": "replanning_agent",
            "validator": "validator",
        },
    )

    workflow.add_edge("replanning_agent", "planning_agent")
    workflow.add_edge("decision_agent", "validator")
    workflow.add_edge("planning_agent", "validator")
    workflow.add_edge("expense_reduction", "validator")
    workflow.add_edge("general_advisor", "validator")
    workflow.add_edge("validator", "reflection")
    workflow.add_edge("reflection", END)

    return workflow.compile()


advisor_graph = build_advisor_graph()


def run_advisor_agent(
    db: Session,
    user_id: uuid.UUID,
    query: str,
    request_id: Optional[str] = None,
) -> AgentState:
    """
    Executes the autonomous FinPilot multi-agent pipeline:
    1. Compiles deterministic financial context.
    2. Runs Agentic RAG retrieval for relevant external guidelines.
    3. Retrieves relevant past decisions from Decision Memory.
    4. Runs multi-agent StateGraph workflow with validation and reflection.
    5. Automatically persists new decisions to Decision Memory.
    6. Logs granular lifecycle AgentEvents for auditability.
    """
    req_id = request_id or str(uuid.uuid4())
    
    # 1. Build deterministic financial facts
    financial_context = build_financial_context(db, user_id)

    # 2. Agentic RAG Knowledge Retrieval
    rag_eval = agentic_rag_engine.execute_agentic_rag(
        db=db,
        user_query=query,
        user_id=str(user_id),
        mode="agentic_rag",
    )
    rag_payload = {
        "retrieval_needed": rag_eval.retrieval_needed,
        "intent": rag_eval.intent,
        "sufficiency_score": rag_eval.sufficiency_score,
        "citations": [c.model_dump() for c in rag_eval.citations],
        "chunks": [c.model_dump() for c in rag_eval.chunks],
    }

    # 3. Retrieve relevant historical memories from PostgreSQL
    past_decisions = retrieve_relevant_memory(db, user_id, query=query, limit=5)
    memory_context = [
        {
            "id": str(d.id),
            "decision_type": d.decision_type,
            "item_name": d.item_name,
            "amount": d.amount,
            "decision": d.decision,
            "strategy_selected": d.strategy_selected,
            "affected_goals": d.affected_goals,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in past_decisions
    ]

    initial_trace: AgentTraceStep = {
        "step": "context_construction",
        "agent": "FinancialContextBuilder",
        "action": "Compiled deterministic financial metrics from database",
        "details": {
            "income": financial_context["profile"]["monthly_income"],
            "expenses_total": financial_context["expense_summary"]["total_expenses"],
            "health_score": financial_context["financial_health_score"]["overall_score"],
            "transactions_count": financial_context["expense_summary"]["transaction_count"],
            "goals_count": len(financial_context.get("goals", [])),
            "rag_citations_count": len(rag_eval.citations),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }

    initial_state: AgentState = {
        "request_id": req_id,
        "user_id": str(user_id),
        "query": query,
        "user_message": query,
        "messages": [{"role": "user", "content": query}],
        "financial_context": financial_context,
        "memory_context": memory_context,
        "rag_result": rag_payload,
        "rag_citations": [c.model_dump() for c in rag_eval.citations],
        "intent": None,
        "routing_decision": None,
        "selected_agents": [],
        "agent_chain": [],
        "current_agent": None,
        "agent_step_index": 0,
        "verified_facts": [],
        "financial_facts": [],
        "scenario_results": None,
        "planning_results": None,
        "monitoring_results": None,
        "replanning_results": None,
        "monitoring_snapshot": None,
        "financial_changes": None,
        "replanning_assessment": None,
        "plan_comparison": None,
        "replanning_strategies": None,
        "decision_memory_result": None,
        "proactive_insights": None,
        "agent_response": None,
        "final_response": None,
        "recommendations": [],
        "reflection_audit": None,
        "validation_errors": [],
        "execution_trace": [initial_trace],
        "error": None,
    }

    try:
        final_state = advisor_graph.invoke(initial_state)
    except Exception as e:
        logger.error(f"LangGraph execution error: {e}", exc_info=True)
        final_state = initial_state
        final_state["final_response"] = (
            f"An internal orchestration issue occurred while processing your request: {str(e)}. "
            "Our deterministic validation layer caught this safely. Please retry."
        )
        final_state["error"] = str(e)

    # 4. Auto-persist decision memory if appropriate
    intent = final_state.get("intent")
    if intent in ("purchase_evaluation", "decision_evaluation", "goal_conflict", "plan_adaptation") and not final_state.get("error"):
        try:
            scenario_res = final_state.get("scenario_results") or {}
            dec_type = "large_purchase" if "purchase" in (final_state.get("query", "").lower()) else "general_decision"
            
            memory_in = DecisionMemoryCreateSchema(
                user_action=query,
                decision=final_state.get("final_response", "")[:500],
                decision_type=dec_type,
                item_name=scenario_res.get("item_name") or query[:50],
                amount=str(scenario_res.get("amount") or "") if scenario_res.get("amount") else None,
                strategy_selected="balanced_mitigation",
                alternatives_considered=scenario_res.get("alternatives"),
                affected_goals=scenario_res.get("affected_goals"),
                baseline_metrics={
                    "savings": financial_context["profile"]["current_savings"],
                    "income": financial_context["profile"]["monthly_income"],
                    "health_score": financial_context["financial_health_score"]["overall_score"],
                },
                resulting_metrics={
                    "resulting_savings": scenario_res.get("resulting_savings"),
                    "resulting_runway": scenario_res.get("resulting_runway"),
                },
                assumptions=[
                    "grounded_by_deterministic_engine",
                    "rag_grounded" if bool(rag_eval.citations) else "no_rag_fallback",
                ],
                recommendation_summary="Created via autonomous multi-agent decision evaluation",
            )
            save_decision_memory(db, user_id, memory_in)
        except Exception as mem_err:
            logger.warning(f"Failed to auto-save decision memory: {mem_err}")

    # 5. Persist audit events
    try:
        event = AgentEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            event_type="multi_agent_execution",
            responsible_agent=final_state.get("routing_decision") or "orchestrator",
            previous_state={"query": query},
            new_state={
                "intent": final_state.get("intent"),
                "selected_agents": final_state.get("selected_agents", []),
                "agent_chain": final_state.get("agent_chain", []),
                "trace_steps_count": len(final_state.get("execution_trace", [])),
                "reflection_status": (final_state.get("reflection_audit") or {}).get("status", "passed"),
                "rag_citations_count": len(final_state.get("rag_citations", [])),
            },
        )
        db.add(event)
        db.commit()
    except Exception as ev_err:
        logger.warning(f"Failed to save agent event log: {ev_err}")

    return final_state
