"""
app/main.py
────────────
FastAPI application factory — Phase 2 complete.
"""
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health, resume, auth, candidates, jobs
from app.core.config import get_settings
from app.core.exceptions import (
    CareerAcceleratorError,
    EmptyPDFError,
    GeminiAPIError,
    GeminiParseError,
    PDFExtractionError,
    PDFTooLargeError,
)
from app.core.logging import configure_logging, get_logger
from app.db.session import create_all_tables

configure_logging()
logger   = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Career Accelerator API [env=%s]", settings.app_env)
    create_all_tables()
    yield
    logger.info("Shutting down AI Career Accelerator API")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Career Accelerator",
        description=(
            "Two-sided talent matchmaking platform. "
            "Phase 2: Auth + Candidate Profiles + Job Postings + AI Matching Engine."
        ),
        version="0.2.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ─────────────────────────────────────────────────────
    @app.exception_handler(PDFTooLargeError)
    async def pdf_too_large_handler(request: Request, exc: PDFTooLargeError):
        return JSONResponse(status_code=413, content={"detail": str(exc), "error_type": "PDFTooLargeError"})

    @app.exception_handler(EmptyPDFError)
    async def empty_pdf_handler(request: Request, exc: EmptyPDFError):
        return JSONResponse(status_code=422, content={"detail": str(exc), "error_type": "EmptyPDFError"})

    @app.exception_handler(PDFExtractionError)
    async def pdf_extraction_handler(request: Request, exc: PDFExtractionError):
        return JSONResponse(status_code=422, content={"detail": str(exc), "error_type": "PDFExtractionError"})

    @app.exception_handler(GeminiAPIError)
    async def gemini_api_handler(request: Request, exc: GeminiAPIError):
        return JSONResponse(status_code=502, content={"detail": str(exc), "error_type": "GeminiAPIError"})

    @app.exception_handler(GeminiParseError)
    async def gemini_parse_handler(request: Request, exc: GeminiParseError):
        return JSONResponse(status_code=502, content={"detail": str(exc), "error_type": "GeminiParseError"})

    @app.exception_handler(CareerAcceleratorError)
    async def base_error_handler(request: Request, exc: CareerAcceleratorError):
        return JSONResponse(status_code=500, content={"detail": str(exc), "error_type": type(exc).__name__})

    # ── Routers ────────────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(resume.router)
    app.include_router(auth.router)
    app.include_router(candidates.router)
    app.include_router(jobs.router)

    return app


app = create_app()