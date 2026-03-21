import logging
import traceback
from datetime import datetime, timezone

from django.db import OperationalError, ProgrammingError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from core.exceptions import AppException

logger = logging.getLogger("apps")


def custom_exception_handler(exc, context):
    request = context.get("request")

    # Layer 1 — DRF known exceptions (400, 401, 403, 404, 405)
    response = exception_handler(exc, context)
    if response is not None:
        data = response.data
        if isinstance(data, dict):
            error_msg = data.get("detail") or data.get("error") or _flatten(data)
        elif isinstance(data, list):
            error_msg = "; ".join(str(e) for e in data)
        else:
            error_msg = str(data)
        response.data = {
            "error":   str(error_msg),
            "message": str(error_msg),
            "status":  response.status_code,
        }
        return response

    # Layer 2 — business AppExceptions
    if isinstance(exc, AppException):
        return Response(
            {"error": str(exc.detail), "message": str(exc.detail), "status": exc.status_code},
            status=exc.status_code,
        )

    # Layer 3 — database errors
    if isinstance(exc, OperationalError):
        _log_exception(exc, request)
        return Response(
            {"error": "Database error. Please try again later.", "message": "Database error. Please try again later.", "status": 503},
            status=503,
        )

    if isinstance(exc, ProgrammingError):
        _log_exception(exc, request)
        return Response(
            {"error": "Database configuration error.", "message": "Database configuration error.", "status": 500},
            status=500,
        )

    # Layer 4 — everything else (AttributeError, TypeError, ZeroDivisionError …)
    _log_exception(exc, request)
    return Response(
        {"error": "Something went wrong. Our team has been notified.", "message": "Something went wrong. Our team has been notified.", "status": 500},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _log_exception(exc: Exception, request=None) -> None:
    try:
        now  = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        tb   = traceback.extract_tb(exc.__traceback__)
        last = tb[-1] if tb else None

        user_id    = "anonymous"
        user_email = "anonymous"
        if request and hasattr(request, "user") and request.user.is_authenticated:
            user_id    = request.user.id
            user_email = request.user.email

        log_msg = (
            "\n╔══════════════════════════════════════════════════════════╗\n"
            "║                   EXCEPTION CAUGHT                      ║\n"
            "╚══════════════════════════════════════════════════════════╝\n"
            f"TIMESTAMP:   {now}\n"
            f"ERROR TYPE:  {type(exc).__name__}\n"
            f"MESSAGE:     {exc}\n"
            f"FILE:        {last.filename if last else 'N/A'}\n"
            f"LINE:        {last.lineno   if last else 'N/A'}\n"
            f"FUNCTION:    {last.name     if last else 'N/A'}\n"
            f"\nREQUEST:\n"
            f"  METHOD: {request.method          if request else 'N/A'}\n"
            f"  URL:    {request.get_full_path() if request else 'N/A'}\n"
            f"\nUSER:\n"
            f"  ID:    {user_id}\n"
            f"  EMAIL: {user_email}\n"
            f"\nSTACK TRACE:\n{traceback.format_exc()}"
            "═══════════════════════════════════════════════════════════"
        )
        logger.error(log_msg)
    except Exception:
        logger.error("Exception logger itself failed", exc_info=True)


def _flatten(data: dict) -> str:
    parts = []
    for field, errors in data.items():
        if isinstance(errors, list):
            parts.append(f"{field}: {', '.join(str(e) for e in errors)}")
        else:
            parts.append(f"{field}: {errors}")
    return "; ".join(parts)