"""FastAPI application entrypoint — PostgreSQL + SQLAlchemy 2.0 async."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.middleware import register_middleware
from backend.app.api.router import api_router
from backend.app.core.logging_config import setup_logging
from backend.app.core.settings import get_settings
from backend.app.db.session import close_db
from backend.app.schemas.api import ApiResponse, ok_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(
        json_format=os.environ.get("GEO_LOG_JSON", "").lower() in ("1", "true", "yes")
    )
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()
    frontend_dir = Path(os.environ.get("GEO_FRONTEND_DIST_DIR", settings.frontend_dist_dir))

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    register_middleware(app)

    @app.get("/", response_model=ApiResponse, tags=["meta"])
    def root() -> ApiResponse:
        return ok_response(
            message="backend_entrypoint_ready",
            data={
                "service": settings.app_name,
                "version": settings.app_version,
                "api_prefix": settings.api_prefix,
            },
        )

    if frontend_dir.exists():
        assets_dir = frontend_dir / "assets"
        if assets_dir.exists():
            app.mount(
                "/console/assets",
                StaticFiles(directory=str(assets_dir)),
                name="console-assets",
            )

        @app.get("/console", include_in_schema=False)
        @app.get("/console/{full_path:path}", include_in_schema=False)
        def console_entry(full_path: str = ""):
            if full_path:
                candidate = (frontend_dir / full_path).resolve()
                if (
                    frontend_dir.resolve() in candidate.parents
                    and candidate.exists()
                    and candidate.is_file()
                ):
                    return FileResponse(candidate)
            return FileResponse(frontend_dir / "index.html")

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
