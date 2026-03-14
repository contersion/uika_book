from collections.abc import Mapping
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


DEFAULT_ERROR_MESSAGE = "Request failed"


def build_error_body(
    *,
    code: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    return {
        "success": False,
        "detail": message,
        "error": {
            "code": code,
            "message": message,
            "details": details,
        },
    }


def build_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: Any = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(build_error_body(code=code, message=message, details=details)),
        headers=dict(headers or {}),
    )


def get_error_message(detail: Any, fallback: str = DEFAULT_ERROR_MESSAGE) -> str:
    if isinstance(detail, str) and detail.strip():
        return detail
    if isinstance(detail, dict):
        message = detail.get("message")
        if isinstance(message, str) and message.strip():
            return message
    return fallback
