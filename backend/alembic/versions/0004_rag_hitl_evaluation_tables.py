"""rag_hitl_evaluation_tables

Revision ID: 0004_rag_hitl_evaluation_tables
Revises: 0003_goals_category_and_contribution
Create Date: 2026-09-27 21:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0004_rag_hitl_evaluation_tables"
down_revision: Union[str, None] = "0003_goals_category_and_contribution"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. knowledge_documents
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", sa.String(length=100), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("publisher", sa.String(length=150), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=False, server_default="general_finance"),
        sa.Column("doc_type", sa.String(length=50), nullable=False, server_default="guide"),
        sa.Column("license", sa.String(length=150), nullable=True),
        sa.Column("publication_date", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_knowledge_documents_source_id", "knowledge_documents", ["source_id"])
    op.create_index("ix_knowledge_documents_title", "knowledge_documents", ["title"])
    op.create_index("ix_knowledge_documents_publisher", "knowledge_documents", ["publisher"])
    op.create_index("ix_knowledge_documents_category", "knowledge_documents", ["category"])

    # 2. knowledge_chunks
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", sa.UUID(as_uuid=True), sa.ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("embedding_json", sa.Text(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_knowledge_chunks_document_id", "knowledge_chunks", ["document_id"])

    # 3. retrieval_events
    op.create_table(
        "retrieval_events",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=100), nullable=False, server_default="general_query"),
        sa.Column("category_filter", sa.String(length=100), nullable=True),
        sa.Column("retrieved_chunk_ids", sa.JSON(), nullable=True),
        sa.Column("sufficiency_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("refinement_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sources_cited", sa.JSON(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_retrieval_events_user_id", "retrieval_events", ["user_id"])

    # 4. recommendation_reviews (HITL)
    op.create_table(
        "recommendation_reviews",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendation_id", sa.String(length=100), nullable=True),
        sa.Column("decision_id", sa.String(length=100), nullable=True),
        sa.Column("agent_name", sa.String(length=100), nullable=False, server_default="Advisor"),
        sa.Column("action", sa.String(length=30), nullable=False, server_default="accepted"),
        sa.Column("user_notes", sa.Text(), nullable=True),
        sa.Column("original_recommendation", sa.JSON(), nullable=True),
        sa.Column("modified_recommendation", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recommendation_reviews_user_id", "recommendation_reviews", ["user_id"])
    op.create_index("ix_recommendation_reviews_recommendation_id", "recommendation_reviews", ["recommendation_id"])
    op.create_index("ix_recommendation_reviews_action", "recommendation_reviews", ["action"])

    # 5. evaluation_runs
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("dataset_name", sa.String(length=100), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=False, server_default="agentic_rag"),
        sa.Column("llm_provider", sa.String(length=50), nullable=False, server_default="groq"),
        sa.Column("model_name", sa.String(length=100), nullable=False, server_default="llama-3.3-70b-versatile"),
        sa.Column("total_cases", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("intent_accuracy", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("tool_selection_accuracy", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("groundedness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("retrieval_relevance", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("structured_output_validity", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reflection_success_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("average_latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("results_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_evaluation_runs_dataset_name", "evaluation_runs", ["dataset_name"])
    op.create_index("ix_evaluation_runs_mode", "evaluation_runs", ["mode"])


def downgrade() -> None:
    op.drop_table("evaluation_runs")
    op.drop_table("recommendation_reviews")
    op.drop_table("retrieval_events")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
