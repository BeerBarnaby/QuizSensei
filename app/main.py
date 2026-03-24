"""
Main entry point for the QuizSensei FastAPI application.
Handles app factory, middleware, router inclusion, and database initialization.
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.routers import documents, export
from app.schemas.assessment.document import HealthResponse
from app.db.session import engine, Base

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    settings = get_settings()
    settings.ensure_upload_dir()
    
    # Initialize DB tables (for MVP, we use create_all instead of Alembic migrations)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "QuizSensei – AI-powered assessment platform. "
        "Phase 1 MVP: document upload service."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request, call_next):
    from app.core.llm import logger
    logger.info(f"REQ: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"RES: {request.method} {request.url.path} -> {response.status_code}")
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(documents.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")


# ── Health check ──────────────────────────────────────────────────────────


# ── Health check ──────────────────────────────────────────────────────────
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["ops"],
    summary="Liveness check",
    description="Returns HTTP 200 when the service is running.",
)
async def health() -> HealthResponse:
    return HealthResponse(app=settings.APP_NAME, version=settings.APP_VERSION)
