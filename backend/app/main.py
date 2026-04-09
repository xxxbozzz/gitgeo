"""FastAPI application entrypoint."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.router import api_router
from backend.app.core.settings import get_settings
from backend.app.schemas.api import ApiResponse, ok_response

FRONTEND_DIST_DIR = Path("/app/frontend_v2_dist")


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

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

    if FRONTEND_DIST_DIR.exists():
        assets_dir = FRONTEND_DIST_DIR / "assets"
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
                candidate = (FRONTEND_DIST_DIR / full_path).resolve()
                if FRONTEND_DIST_DIR.resolve() in candidate.parents and candidate.exists() and candidate.is_file():
                    return FileResponse(candidate)
            return FileResponse(FRONTEND_DIST_DIR / "index.html")

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
