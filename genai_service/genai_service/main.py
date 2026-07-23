"""FastAPI application factory and entrypoint for GenAI Interview Service."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from genai_service.config import get_settings
from genai_service.routers import dashboard, interview, resume
from genai_service.schemas.api import ErrorResponse, HealthResponse
from genai_service.utils.exceptions import InterviewEngineError
from genai_service.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    settings = get_settings()
    logger.info(
        "genai_service_startup",
        environment=settings.environment,
        llm_model=settings.groq_model,
        port=settings.service_port,
    )
    yield
    logger.info("genai_service_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Standalone GenAI Interview Service — "
            "Multi-Agent AI Interview Engine (Groq + LangGraph + FastAPI). "
            "No database dependency. Fully in-memory."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers at both root and /api/v1
    for p in ("", "/api/v1"):
        app.include_router(resume.router, prefix=p)
        app.include_router(interview.router, prefix=p)
        app.include_router(dashboard.router, prefix=p)

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health() -> HealthResponse:
        s = get_settings()
        return HealthResponse(
            status="ok",
            version=s.app_version,
            environment=s.environment,
            llm_model=s.groq_model,
        )

    @app.get("/", tags=["Health"])
    async def root() -> dict[str, Any]:
        return {
            "success": True,
            "service": "GenAI Interview Service",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
            "endpoints": {
                "upload_resume": "POST /api/v1/upload_resume",
                "start_interview": "POST /api/v1/start_interview",
                "next_question": "POST /api/v1/next_question",
                "submit_answer": "POST /api/v1/submit_answer",
                "end_interview": "POST /api/v1/end_interview",
                "get_interview": "GET /api/v1/interview/{interview_id}",
                "list_candidates": "GET /api/v1/dashboard/candidates",
                "chat_history": "GET /api/v1/dashboard/chat-history/{interview_id}",
                "dashboard": "GET /api/v1/dashboard/{candidate_id}",
            },
        }

    @app.exception_handler(InterviewEngineError)
    async def engine_error_handler(
        _request: Request, exc: InterviewEngineError
    ) -> JSONResponse:
        status = 400
        name = type(exc).__name__
        if name == "SessionNotFoundError":
            status = 404
        elif name == "ConfigurationError":
            status = 500
        elif name == "LLMError":
            status = 502
        elif name == "InterviewLimitReachedError":
            status = 409
        body = ErrorResponse(
            success=False,
            message=exc.message,
            errors=[name],
            detail=exc.details,
        )
        return JSONResponse(status_code=status, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        body = ErrorResponse(
            success=False,
            message="Validation error",
            errors=[str(e) for e in exc.errors()],
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", error=str(exc))
        body = ErrorResponse(
            success=False,
            message="Internal server error",
            errors=[type(exc).__name__],
            detail=str(exc) if settings.debug else None,
        )
        return JSONResponse(status_code=500, content=body.model_dump())

    return app


app = create_app()
