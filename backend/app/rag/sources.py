from typing import Any, Dict, List
from sqlalchemy.orm import Session

from app.models.rag import KnowledgeDocument


def list_knowledge_sources(db: Session) -> List[Dict[str, Any]]:
    """Retrieve catalog of all ingested knowledge documents."""
    docs = db.query(KnowledgeDocument).all()
    return [
        {
            "id": str(d.id),
            "source_id": d.source_id,
            "title": d.title,
            "publisher": d.publisher,
            "category": d.category,
            "doc_type": d.doc_type,
            "url": d.url,
            "license": d.license,
            "publication_date": d.publication_date,
            "chunks_count": len(d.chunks),
        }
        for d in docs
    ]
