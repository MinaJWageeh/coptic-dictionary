"""Application exceptions and a unified exception handler.

Errors are returned in the shape:
    {"error": {"code": "...", "message": "...", "details": {...}}}
"""
from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error. Subclasses set `status` and `code`."""

    status: int = 400
    code: str = "APP_ERROR"

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    status = 404
    code = "NOT_FOUND"


class AuthError(AppError):
    status = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppError):
    status = 403
    code = "FORBIDDEN"


class ValidationError(AppError):
    status = 422
    code = "VALIDATION_ERROR"


class ConflictError(AppError):
    status = 409
    code = "CONFLICT"


def error_payload(err: AppError) -> dict[str, Any]:
    return {
        "error": {
            "code": err.code,
            "message": err.message,
            "details": err.details,
        }
    }
