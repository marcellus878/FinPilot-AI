from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    id: str
    question: str
    expected_intent: str
    expected_tools: List[str] = Field(default_factory=list)
    expected_retrieval_need: bool = False
    expected_source_category: Optional[str] = None
    expected_key_facts: List[str] = Field(default_factory=list)
    evaluation_notes: Optional[str] = None


class CaseResult(BaseModel):
    case_id: str
    question: str
    intent_match: bool
    tool_match: bool
    retrieval_correctness: bool
    groundedness_score: float
    reflection_success: bool
    latency_ms: float
    sources_cited: List[str] = Field(default_factory=list)
    generated_content_excerpt: str


class EvaluationSummary(BaseModel):
    dataset_name: str
    mode: str  # "no_rag", "basic_rag", "agentic_rag"
    llm_provider: str
    model_name: str
    total_cases: int
    intent_accuracy: float
    tool_selection_accuracy: float
    groundedness_score: float
    retrieval_relevance: float
    structured_output_validity: float
    reflection_success_rate: float
    average_latency_ms: float
    case_results: List[CaseResult] = Field(default_factory=list)


class RAGModeComparisonResult(BaseModel):
    no_rag: EvaluationSummary
    basic_rag: EvaluationSummary
    agentic_rag: EvaluationSummary
    comparative_insights: List[str] = Field(default_factory=list)


class LLMComparisonItem(BaseModel):
    model_name: str
    provider: str
    factual_accuracy: float
    groundedness_score: float
    structured_output_validity: float
    average_latency_ms: float
    token_efficiency: float
    cost_tier: str


class LLMBenchmarkResult(BaseModel):
    models: List[LLMComparisonItem]
    benchmarked_dataset: str
    timestamp: str
