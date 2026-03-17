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
from app.routers.teacher import documents as teacher_docs, export as teacher_export
from app.schemas.teacher.document import HealthResponse
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(teacher_docs.router, prefix="/api/v1/teacher")
app.include_router(teacher_export.router, prefix="/api/v1/teacher")


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
