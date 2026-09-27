from typing import Any, Dict, List, Optional, TypedDict


class AgentTraceStep(TypedDict, total=False):
    step: str
    agent: str
    action: str
    details: Dict[str, Any]
    timestamp: str


class FinancialFact(TypedDict, total=False):
    metric: str
    value: Any
    category: Optional[str]
    interpretation: Optional[str]


class AgentRecommendation(TypedDict, total=False):
    id: Optional[str]
    type: str  # "expense_reduction", "budget_adjustment", "goal_acceleration", "habit_change", "general"
    title: str
    description: str
    potential_monthly_savings: Optional[float]
    priority: str  # "high", "medium", "low"
    category: Optional[str]
    hitl_status: Optional[str]  # "pending_review", "accepted", "modified", "rejected"


class RAGCitationItem(TypedDict, total=False):
    source_id: str
    title: str
    publisher: str
    category: str
    url: Optional[str]
    relevant_excerpt: str


class ReflectionAudit(TypedDict, total=False):
    status: str  # "passed", "corrected"
    groundedness_score: float
    issues_detected: List[str]
    corrections_applied: List[str]
    reflection_performed: bool
    rag_grounded: bool


class AgentState(TypedDict, total=False):
    # Context & Identifiers
    request_id: str
    user_id: str
    query: str
    user_message: Optional[str]
    messages: List[Dict[str, str]]
    
    # Deterministic Financial & Memory Context
    financial_context: Dict[str, Any]
    memory_context: Optional[List[Dict[str, Any]]]
    
    # Agentic RAG Knowledge & Retrieval
    rag_result: Optional[Dict[str, Any]]
    rag_citations: Optional[List[RAGCitationItem]]
    
    # Orchestration & Multi-Agent Routing
    intent: Optional[str]
    routing_decision: Optional[str]
    selected_agents: List[str]
    agent_chain: List[str]
    current_agent: Optional[str]
    agent_step_index: int
    prompt_versions: Optional[Dict[str, str]]
    
    # Verified Facts & Intermediate Results
    verified_facts: List[FinancialFact]
    financial_facts: List[FinancialFact]
    scenario_results: Optional[Dict[str, Any]]
    planning_results: Optional[Dict[str, Any]]
    monitoring_results: Optional[Dict[str, Any]]
    replanning_results: Optional[Dict[str, Any]]
    
    # Monitoring & Replanning State
    monitoring_snapshot: Optional[Dict[str, Any]]
    financial_changes: Optional[List[Dict[str, Any]]]
    replanning_assessment: Optional[Dict[str, Any]]
    plan_comparison: Optional[Dict[str, Any]]
    replanning_strategies: Optional[List[Dict[str, Any]]]
    
    # Decision Memory & Proactive Insights
    decision_memory_result: Optional[Dict[str, Any]]
    proactive_insights: Optional[List[Dict[str, Any]]]
    
    # Agent Outputs & Recommendations
    agent_response: Optional[str]
    final_response: Optional[str]
    recommendations: List[AgentRecommendation]
    
    # Reflection & Self-Correction
    reflection_audit: Optional[ReflectionAudit]
    
    # Validation & Lifecycle Tracing
    validation_errors: Optional[List[str]]
    execution_trace: List[AgentTraceStep]
    error: Optional[str]
