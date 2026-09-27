import re
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.models.rag import KnowledgeChunk, KnowledgeDocument
from app.rag.embeddings import embedding_service
from app.rag.schemas import KnowledgeChunkItem, RAGCitation


class HybridKnowledgeRetriever:
    """
    Hybrid vector similarity + keyword matcher for FinPilot RAG knowledge base.
    """

    def retrieve(
        self,
        db: Session,
        query: str,
        category_filter: Optional[str] = None,
        top_k: int = 3,
        similarity_threshold: float = 0.15,
    ) -> List[KnowledgeChunkItem]:
        """
        Retrieve relevant knowledge chunks matching the query.
        Combines dense vector similarity with keyword tag bonuses.
        """
        if not query or not query.strip():
            return []

        query_vector = embedding_service.generate_embedding(query)
        query_terms = set(re.findall(r"\b[a-zA-Z0-9_\$₹\.-]{3,}\b", query.lower()))

        # Query chunks with joined document metadata
        chunk_query = db.query(KnowledgeChunk).options(joinedload(KnowledgeChunk.document))
        if category_filter and category_filter != "all":
            chunk_query = chunk_query.join(KnowledgeDocument).filter(KnowledgeDocument.category == category_filter)

        all_chunks = chunk_query.all()
        if not all_chunks:
            return []

        scored_results = []
        for chunk in all_chunks:
            chunk_vector = embedding_service.deserialize_vector(chunk.embedding_json or "")
            cos_sim = embedding_service.cosine_similarity(query_vector, chunk_vector)

            # Keyword overlap bonus
            chunk_text_lower = chunk.chunk_text.lower()
            metadata = chunk.metadata_json or {}
            tags = metadata.get("tags", [])
            tag_overlap = sum(1 for tag in tags if tag.lower() in query_terms)
            keyword_overlap = sum(1 for term in query_terms if term in chunk_text_lower)

            keyword_bonus = min(0.3, (tag_overlap * 0.1) + (keyword_overlap * 0.02))
            final_score = min(1.0, cos_sim + keyword_bonus)

            if final_score >= similarity_threshold:
                doc = chunk.document
                scored_results.append(
                    KnowledgeChunkItem(
                        chunk_id=metadata.get("chunk_id", str(chunk.id)),
                        document_id=str(doc.id) if doc else None,
                        source_id=doc.source_id if doc else "unknown",
                        source_title=doc.title if doc else "Financial Guidelines",
                        publisher=doc.publisher if doc else "Official",
                        category=doc.category if doc else "general_finance",
                        chunk_index=chunk.chunk_index,
                        chunk_text=chunk.chunk_text,
                        similarity_score=round(final_score, 4),
                        url=doc.url if doc else None,
                        tags=tags,
                    )
                )

        # Sort descending by score
        scored_results.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored_results[:top_k]

    def build_citations(self, chunks: List[KnowledgeChunkItem]) -> List[RAGCitation]:
        """Convert retrieved chunks to clean UI-ready citations."""
        citations = []
        seen_sources = set()
        for c in chunks:
            if c.source_id in seen_sources:
                continue
            seen_sources.add(c.source_id)
            # Create a concise excerpt
            excerpt = c.chunk_text[:180] + ("..." if len(c.chunk_text) > 180 else "")
            citations.append(
                RAGCitation(
                    source_id=c.source_id,
                    title=c.source_title,
                    publisher=c.publisher,
                    category=c.category,
                    url=c.url,
                    relevant_excerpt=excerpt,
                )
            )
        return citations


# Global singleton retriever
knowledge_retriever = HybridKnowledgeRetriever()
