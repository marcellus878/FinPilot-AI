import uuid
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.evaluation.evaluator import agent_evaluator
from app.evaluation.llm_comparator import llm_comparator
from app.evaluation.schemas import LLMBenchmarkResult, RAGModeComparisonResult
from app.models.evaluation import EvaluationRun


class EvaluationService:
    """Service layer to run evaluations and persist benchmark runs."""

    def run_and_persist_evaluation(
        self,
        db: Session,
        dataset_name: str = "rag_questions.jsonl",
        mode: str = "agentic_rag",
    ) -> Dict[str, Any]:
        eval_summary = agent_evaluator.run_evaluation(db=db, dataset_name=dataset_name, mode=mode)

        try:
            record = EvaluationRun(
                id=uuid.uuid4(),
                dataset_name=dataset_name,
                mode=mode,
                llm_provider=eval_summary.llm_provider,
                model_name=eval_summary.model_name,
                total_cases=eval_summary.total_cases,
                intent_accuracy=eval_summary.intent_accuracy,
                tool_selection_accuracy=eval_summary.tool_selection_accuracy,
                groundedness_score=eval_summary.groundedness_score,
                retrieval_relevance=eval_summary.retrieval_relevance,
                structured_output_validity=eval_summary.structured_output_validity,
                reflection_success_rate=eval_summary.reflection_success_rate,
                average_latency_ms=eval_summary.average_latency_ms,
                results_json={
                    "cases_count": eval_summary.total_cases,
                    "cases": [c.model_dump() for c in eval_summary.case_results],
                },
            )
            db.add(record)
            db.commit()
        except Exception as e:
            db.rollback()

        return eval_summary.model_dump()

    def get_rag_comparison(self, db: Session) -> RAGModeComparisonResult:
        return agent_evaluator.compare_rag_modes(db=db)

    def get_llm_benchmarks(self) -> LLMBenchmarkResult:
        return llm_comparator.get_benchmark_results()


evaluation_service = EvaluationService()
