from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.evaluation.schemas import LLMBenchmarkResult, RAGModeComparisonResult
from app.evaluation.service import evaluation_service

router = APIRouter()


class RunEvaluationIn(BaseModel):
    dataset_name: str = "rag_questions.jsonl"
    mode: str = "agentic_rag"  # "no_rag", "basic_rag", "agentic_rag"


@router.post("/run")
def run_evaluation_benchmark(
    payload: RunEvaluationIn,
    db: Session = Depends(get_db),
):
    """Run an evaluation benchmark across a dataset."""
    return evaluation_service.run_and_persist_evaluation(
        db=db,
        dataset_name=payload.dataset_name,
        mode=payload.mode,
    )


@router.get("/rag-comparison", response_model=RAGModeComparisonResult)
def get_rag_comparison(
    dataset_name: str = Query("rag_questions.jsonl"),
    db: Session = Depends(get_db),
):
    """Run and return multi-mode comparison: No RAG vs Basic RAG vs Agentic RAG."""
    return evaluation_service.get_rag_comparison(db=db)


@router.get("/llm-benchmark", response_model=LLMBenchmarkResult)
def get_llm_benchmark():
    """Retrieve multi-model LLM benchmark results."""
    return evaluation_service.get_llm_benchmarks()
