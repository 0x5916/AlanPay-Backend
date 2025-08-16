from fastapi import APIRouter, FastAPI, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime
from app.utils.database import AsyncSessionDep
from sqlalchemy import text
from app.utils.logging_config import logger


router = APIRouter(prefix="/api", tags=["health"])

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    database_status: str
    version: str

cached_statement = text("SELECT 1")

@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request, session: AsyncSessionDep):
    try:
        # Test database connection
        app: FastAPI = request.app
        await session.execute(cached_statement)
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            database_status="healthy",
            version=app.version
        )
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )

@router.get("/ping")
async def ping():
    return {"message": "pong", "timestamp": datetime.now()}
