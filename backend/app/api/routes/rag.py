from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.rag import agentic_rag_engine, knowledge_pipeline, list_knowledge_sources
from app.rag.schemas import RAGRetrievalResult

router = APIRouter()


class RAGQueryIn(BaseModel):
    query: str
    category: Optional[str] = None
    mode: str = "agentic_rag"  # "no_rag", "basic_rag", "agentic_rag"
    top_k: int = 3


@router.get("/sources", response_model=List[Dict[str, Any]])
def get_rag_sources(db: Session = Depends(get_db)):
    """Return catalog of all ingested authoritative public knowledge sources."""
    return list_knowledge_sources(db)


@router.post("/query", response_model=RAGRetrievalResult)
def query_rag_knowledge(
    payload: RAGQueryIn,
    db: Session = Depends(get_db),
):
    """Query knowledge base using Agentic RAG."""
    return agentic_rag_engine.execute_agentic_rag(
        db=db,
        user_query=payload.query,
        top_k=payload.top_k,
        mode=payload.mode,
    )


@router.post("/reingest")
def reingest_knowledge(db: Session = Depends(get_db)):
    """Re-ingest all dataset files from datasets/knowledge_base/."""
    result = knowledge_pipeline.ingest_all_datasets(db)
    return {"status": "success", "result": result}
