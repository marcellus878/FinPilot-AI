from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    source_id: str
    title: str
    publisher: str
    url: Optional[str] = None
    category: str = "general_finance"
    doc_type: str = "guide"
    license: Optional[str] = None
    publication_date: Optional[str] = None


class KnowledgeChunkItem(BaseModel):
    chunk_id: str
    document_id: Optional[str] = None
    source_id: str
    source_title: str
    publisher: str
    category: str
    chunk_index: int
    chunk_text: str
    similarity_score: float = 0.0
    url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class RAGCitation(BaseModel):
    source_id: str
    title: str
    publisher: str
    category: str
    url: Optional[str] = None
    relevant_excerpt: str


class RAGQueryRequest(BaseModel):
    query: str
    category_filter: Optional[str] = None
    top_k: int = 3
    similarity_threshold: float = 0.25


class RAGRetrievalResult(BaseModel):
    query: str
    intent: str
    retrieval_needed: bool = True
    chunks: List[KnowledgeChunkItem] = Field(default_factory=list)
    citations: List[RAGCitation] = Field(default_factory=list)
    sufficiency_score: float = 1.0
    refinement_count: int = 0
    latency_ms: float = 0.0
