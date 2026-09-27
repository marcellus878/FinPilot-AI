import logging
import time
import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.rag import RetrievalEvent
from app.rag.retriever import knowledge_retriever
from app.rag.schemas import KnowledgeChunkItem, RAGCitation, RAGRetrievalResult

logger = logging.getLogger(__name__)


class AgenticRetrievalEngine:
    """
    Agentic RAG Engine:
    Decides necessity, crafts queries, verifies sufficiency, and refines search iteratively.
    """

    KNOWLEDGE_INTENT_KEYWORDS = {
        "financial_literacy": ["rbi", "rule", "guideline", "standard", "official", "law", "policy"],
        "debt_and_reserves": ["debt", "avalanche", "snowball", "emergency", "runway", "loan", "emi", "interest", "credit card"],
        "goal_planning": ["sebi", "goal", "horizon", "priority", "conflict", "timeline", "asset", "invest"],
        "personal_budgeting": ["50/30/20", "50-30-20", "budget", "allocation", "tax", "ppf", "nps", "safe to spend", "inr"],
    }

    def evaluate_retrieval_need(self, user_query: str) -> Dict[str, Any]:
        """
        Agentic Decision: Does this question require external financial principles / guidelines?
        """
        query_lower = user_query.lower()
        matched_categories = []
        for cat, keywords in self.KNOWLEDGE_INTENT_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                matched_categories.append(cat)

        # General financial planning concepts that trigger RAG
        general_triggers = ["how should i", "what is the rule", "best way to", "can i afford", "guideline", "strategy", "recommend"]
        needs_rag = len(matched_categories) > 0 or any(t in query_lower for t in general_triggers)

        category = matched_categories[0] if matched_categories else "all"
        return {
            "retrieval_needed": needs_rag,
            "target_category": category,
            "intent": "conceptual_advisory" if needs_rag else "user_math_only",
        }

    def generate_refined_query(self, user_query: str, target_category: str) -> str:
        """
        Craft targeted domain search query.
        """
        query_lower = user_query.lower()
        if "laptop" in query_lower or "purchase" in query_lower or "afford" in query_lower:
            return "large purchase affordability emergency reserve buffer goal delay rule"
        elif "debt" in query_lower or "loan" in query_lower or "emi" in query_lower:
            return "debt avalanche snowball repayment credit utilization foir rbi"
        elif "salary" in query_lower or "allocate" in query_lower or "50/30/20" in query_lower:
            return "50/30/20 rule salary allocation essential living commitments discretionary"
        elif "emergency" in query_lower or "buffer" in query_lower or "shock" in query_lower:
            return "emergency reserve fund 3 to 6 months liquid savings rbi guidance"
        elif "conflict" in query_lower or "competing" in query_lower or "goals" in query_lower:
            return "competing goals priority ranking discretionary timeline extension sebi"
        return user_query

    def execute_agentic_rag(
        self,
        db: Session,
        user_query: str,
        user_id: Optional[str] = None,
        top_k: int = 3,
        mode: str = "agentic_rag",
    ) -> RAGRetrievalResult:
        """
        Execute RAG workflow based on mode:
        - mode='no_rag': returns empty retrieval
        - mode='basic_rag': direct query to vector search without agentic loops
        - mode='agentic_rag': full agentic loop (decision -> query refinement -> verification -> citation)
        """
        start_time = time.time()

        if mode == "no_rag":
            return RAGRetrievalResult(
                query=user_query,
                intent="no_rag_mode",
                retrieval_needed=False,
                chunks=[],
                citations=[],
                sufficiency_score=0.0,
                refinement_count=0,
                latency_ms=0.0,
            )

        if mode == "basic_rag":
            # Simple direct vector search
            chunks = knowledge_retriever.retrieve(
                db=db,
                query=user_query,
                category_filter=None,
                top_k=top_k,
                similarity_threshold=0.1,
            )
            citations = knowledge_retriever.build_citations(chunks)
            latency = (time.time() - start_time) * 1000
            return RAGRetrievalResult(
                query=user_query,
                intent="basic_rag_lookup",
                retrieval_needed=True,
                chunks=chunks,
                citations=citations,
                sufficiency_score=1.0 if chunks else 0.0,
                refinement_count=0,
                latency_ms=round(latency, 2),
            )

        # Agentic RAG Mode:
        # Step 1: Decision
        decision = self.evaluate_retrieval_need(user_query)
        if not decision["retrieval_needed"]:
            latency = (time.time() - start_time) * 1000
            return RAGRetrievalResult(
                query=user_query,
                intent=decision["intent"],
                retrieval_needed=False,
                chunks=[],
                citations=[],
                sufficiency_score=1.0,
                refinement_count=0,
                latency_ms=round(latency, 2),
            )

        # Step 2: Query Generation
        target_category = decision["target_category"]
        search_query = self.generate_refined_query(user_query, target_category)

        # Step 3: Retrieval (Pass 1)
        chunks = knowledge_retriever.retrieve(
            db=db,
            query=search_query,
            category_filter=target_category if target_category != "all" else None,
            top_k=top_k,
            similarity_threshold=0.2,
        )

        refinements = 0
        # Step 4 & 5: Relevance Check & Refinement
        if not chunks or (chunks and chunks[0].similarity_score < 0.35):
            refinements += 1
            # Broaden search to all categories and fallback terms
            chunks = knowledge_retriever.retrieve(
                db=db,
                query=user_query,
                category_filter=None,
                top_k=top_k,
                similarity_threshold=0.15,
            )

        citations = knowledge_retriever.build_citations(chunks)
        top_score = chunks[0].similarity_score if chunks else 0.0
        sufficiency = min(1.0, top_score / 0.5) if chunks else 0.0
        latency = (time.time() - start_time) * 1000

        # Record Retrieval Event in DB
        try:
            event = RetrievalEvent(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id) if user_id else None,
                query=user_query,
                intent=decision["intent"],
                category_filter=target_category,
                retrieved_chunk_ids=[c.chunk_id for c in chunks],
                sufficiency_score=round(sufficiency, 3),
                refinement_count=refinements,
                sources_cited=[c.model_dump() for c in citations],
                latency_ms=round(latency, 2),
            )
            db.add(event)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Could not record retrieval event: {e}")

        return RAGRetrievalResult(
            query=user_query,
            intent=decision["intent"],
            retrieval_needed=True,
            chunks=chunks,
            citations=citations,
            sufficiency_score=round(sufficiency, 3),
            refinement_count=refinements,
            latency_ms=round(latency, 2),
        )


# Global singleton agentic RAG engine
agentic_rag_engine = AgenticRetrievalEngine()
