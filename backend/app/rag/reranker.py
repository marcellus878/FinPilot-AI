from typing import List
from app.rag.schemas import KnowledgeChunkItem


class ScoreReranker:
    """
    Reranks retrieved knowledge chunks based on query term coverage and authoritative source weightings.
    """

    AUTHORITY_WEIGHTS = {
        "Reserve Bank of India (RBI)": 1.15,
        "Securities and Exchange Board of India (SEBI)": 1.15,
        "National Institute of Financial Management & Indian Personal Finance Standards": 1.10,
        "Financial Planning Standards Board & Consumer Finance Education": 1.10,
    }

    def rerank(self, chunks: List[KnowledgeChunkItem], query: str) -> List[KnowledgeChunkItem]:
        """Apply publisher authority multiplier and sort chunks."""
        if not chunks:
            return []

        for chunk in chunks:
            multiplier = self.AUTHORITY_WEIGHTS.get(chunk.publisher, 1.0)
            chunk.similarity_score = min(1.0, round(chunk.similarity_score * multiplier, 4))

        chunks.sort(key=lambda x: x.similarity_score, reverse=True)
        return chunks


reranker = ScoreReranker()
