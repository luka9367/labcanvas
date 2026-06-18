"""FastAPI main application."""

import logging
import time
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings, STATIC_DIR, CORS_ORIGINS, API_V1_PREFIX
from app.api.v1.router import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    # Initialize default reference images
    try:
        from app.services import references_service
        references_service.init_default_references()
        print("Default reference images initialized")
    except Exception as e:
        print(f"Warning: Failed to initialize default references: {e}")
    
    # Initialize gallery images
    try:
        from app.services import gallery_images_service
        gallery_images_service.init_gallery_images()
        print("Gallery images initialized")
    except Exception as e:
        print(f"Warning: Failed to initialize gallery images: {e}")
    
    yield
    # Shutdown
    logger.info("Shutting down LabCanvas API server")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    # Global exception handling middleware — catches ALL unhandled exceptions
    # to prevent the entire server from crashing on a single bad request.
    @app.middleware("http")
    async def global_error_handler(request: Request, call_next):
        start_time = time.time()
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response
        except Exception as exc:
            process_time = time.time() - start_time
            logger.error(
                "Unhandled exception in %s %s after %.3fs: %s\n%s",
                request.method,
                request.url.path,
                process_time,
                str(exc),
                traceback.format_exc(),
            )
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "服务暂时不可用，请稍后重试",
                    "type": "internal_server_error",
                },
            )

    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(
            "%s %s - %d - %.3fs",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )
        return response

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router, prefix=API_V1_PREFIX)

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": settings.VERSION}

    @app.get("/api/v1/health")
    async def api_health_check():
        return {"status": "ok", "version": settings.VERSION}

    # Static files (serve frontend at root, after API routes so API takes precedence)
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


app = create_app()
