import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.responses import build_error_response, get_error_message


logger = logging.getLogger(__name__)


DEFAULT_HTTP_ERROR_MESSAGE = "Request failed"
VALIDATION_ERROR_MESSAGE = "Request validation failed"
INTERNAL_ERROR_MESSAGE = "Internal server error"


def register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException):
        detail: Any = exc.detail
        message = get_error_message(detail, fallback=DEFAULT_HTTP_ERROR_MESSAGE)
        details = None if isinstance(detail, str) else detail
        return build_error_response(
            status_code=exc.status_code,
            code=f"http_{exc.status_code}",
            message=message,
            details=details,
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        return build_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            code="validation_error",
            message=VALIDATION_ERROR_MESSAGE,
            details=exc.errors(),
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled application error on %s", request.url.path, exc_info=exc)
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="internal_server_error",
            message=INTERNAL_ERROR_MESSAGE,
        )
