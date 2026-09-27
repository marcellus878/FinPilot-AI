from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.database import Base, engine
import app.models  # noqa: F401 - Register all models


import os
from alembic.config import Config
from alembic import command


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is migrated to head on startup
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alembic_ini_path = os.path.join(backend_dir, "alembic.ini")
        if os.path.exists(alembic_ini_path):
            alembic_cfg = Config(alembic_ini_path)
            alembic_cfg.set_main_option("sqlalchemy.url", settings.sync_database_url)
            command.upgrade(alembic_cfg, "head")
        else:
            Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Database migration error on startup: {e}")
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as create_err:
            print(f"Warning: Fallback create_all failed: {create_err}")

    # Ingest authoritative knowledge datasets into RAG store
    try:
        from app.core.database import SessionLocal
        from app.rag.ingestion import knowledge_pipeline
        with SessionLocal() as db:
            ingest_result = knowledge_pipeline.ingest_all_datasets(db)
            print(f"RAG Knowledge Base ready: {ingest_result}")
    except Exception as rag_err:
        print(f"Warning: Knowledge base ingestion note: {rag_err}")

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
)

# Set up CORS middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Root-level health endpoint & API router
app.include_router(health_router, tags=["health"])
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["root"])
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs" if settings.DEBUG else None,
        "health": "/health",
    }
