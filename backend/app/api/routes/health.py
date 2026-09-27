from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    environment: str
    version: str
    project: str


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        project=settings.PROJECT_NAME,
    )
