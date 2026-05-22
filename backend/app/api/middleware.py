"""FastAPI middleware stack."""

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.app.core.exceptions import AppError
from backend.app.schemas.api import fail_response

logger = logging.getLogger("geo_backend.api")


def register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled exception request_id=%s path=%s", request_id, request.url.path)
            response = JSONResponse(
                status_code=500,
                content=fail_response(
                    message="Internal server error",
                    error_code="internal_error",
                ).model_dump(),
            )
        elapsed_ms = (time.monotonic() - start) * 1000

        logger.info(
            "request_id=%s method=%s path=%s status=%d elapsed_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.warning(
            "AppError request_id=%s path=%s error_code=%s message=%s",
            getattr(request.state, "request_id", "-"),
            request.url.path,
            exc.error_code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=fail_response(
                message=exc.message,
                error_code=exc.error_code,
            ).model_dump(),
        )
