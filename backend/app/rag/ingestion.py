import json
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.rag import KnowledgeChunk, KnowledgeDocument
from app.rag.embeddings import embedding_service

logger = logging.getLogger(__name__)

DATASETS_DIR = Path(__file__).resolve().parents[3] / "datasets" / "knowledge_base"


class KnowledgeIngestionPipeline:
    """
    Ingests external authoritative knowledge base files into PostgreSQL/SQLite RAG store.
    """

    def __init__(self, datasets_path: Optional[Path] = None):
        self.datasets_path = datasets_path or DATASETS_DIR

    def ingest_all_datasets(self, db: Session) -> Dict[str, int]:
        """
        Scan and ingest all JSON dataset files from the knowledge base directory.
        Returns counts of documents and chunks ingested.
        """
        if not self.datasets_path.exists():
            logger.warning(f"Datasets directory not found at {self.datasets_path}")
            return {"documents_ingested": 0, "chunks_ingested": 0}

        docs_count = 0
        chunks_count = 0

        for file_path in self.datasets_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                source_id = data.get("source_id")
                if not source_id:
                    continue

                # Check if document already exists
                doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.source_id == source_id).first()
                if not doc:
                    doc = KnowledgeDocument(
                        id=uuid.uuid4(),
                        source_id=source_id,
                        title=data.get("title", "Financial Knowledge Document"),
                        publisher=data.get("publisher", "Official Publisher"),
                        url=data.get("url"),
                        category=data.get("category", "general_finance"),
                        doc_type=data.get("doc_type", "guide"),
                        license=data.get("license"),
                        publication_date=str(data.get("publication_date", "")),
                    )
                    db.add(doc)
                    db.flush()
                    docs_count += 1
                else:
                    # Update metadata
                    doc.title = data.get("title", doc.title)
                    doc.publisher = data.get("publisher", doc.publisher)
                    doc.category = data.get("category", doc.category)
                    doc.url = data.get("url", doc.url)

                # Ingest chunks
                chunks_data = data.get("chunks", [])
                for idx, chunk_info in enumerate(chunks_data):
                    chunk_text = chunk_info.get("text", "")
                    if not chunk_text:
                        continue

                    # Check if chunk already exists
                    existing_chunk = (
                        db.query(KnowledgeChunk)
                        .filter(
                            KnowledgeChunk.document_id == doc.id,
                            KnowledgeChunk.chunk_index == idx,
                        )
                        .first()
                    )

                    vector = embedding_service.generate_embedding(chunk_text)
                    vector_str = embedding_service.serialize_vector(vector)

                    if not existing_chunk:
                        new_chunk = KnowledgeChunk(
                            id=uuid.uuid4(),
                            document_id=doc.id,
                            chunk_index=idx,
                            chunk_text=chunk_text,
                            embedding_json=vector_str,
                            token_count=len(chunk_text.split()),
                            metadata_json={
                                "chunk_id": chunk_info.get("chunk_id", f"{source_id}-{idx}"),
                                "title": chunk_info.get("title", ""),
                                "tags": chunk_info.get("tags", []),
                            },
                        )
                        db.add(new_chunk)
                        chunks_count += 1
                    else:
                        existing_chunk.chunk_text = chunk_text
                        existing_chunk.embedding_json = vector_str
                        existing_chunk.metadata_json = {
                            "chunk_id": chunk_info.get("chunk_id", f"{source_id}-{idx}"),
                            "title": chunk_info.get("title", ""),
                            "tags": chunk_info.get("tags", []),
                        }

                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error ingesting {file_path.name}: {e}")

        return {"documents_ingested": docs_count, "chunks_ingested": chunks_count}


# Singleton pipeline
knowledge_pipeline = KnowledgeIngestionPipeline()
