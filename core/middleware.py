import time
import uuid
import logging
from datetime import datetime, timezone

from core.utils import get_client_ip, mask_phone, mask_token, safe_request_body

logger = logging.getLogger("api")

BORDER = "*" * 65


def _headers_clean(headers_obj) -> dict:
    result = {}
    for key, value in dict(headers_obj).items():
        if key.lower() in ("authorization", "cookie"):
            result[key] = mask_token(value)
        else:
            result[key] = value
    return result


def _user_line(request) -> str:
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return "anonymous"
    phone     = getattr(user, "phone",     None) or "N/A"
    community = getattr(user, "community", None) or "N/A"
    role      = getattr(user, "role",      None) or "N/A"
    return (
        f"Id: {user.id}  |  "
        f"Email: {user.email}  |  "
        f"Phone: {mask_phone(str(phone))}  |  "
        f"Role: {role}  |  "
        f"Community: {community}"
    )


def _response_message(response) -> str:
    data = getattr(response, "data", None)
    if isinstance(data, dict):
        msg = data.get("message") or data.get("error") or data.get("detail") or ""
        return str(msg)
    return ""


def _format_size(num_bytes: int) -> str:
    if num_bytes < 1024:
        return f"{num_bytes} B"
    elif num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


class RequestLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._request_id  = uuid.uuid4().hex[:8].upper()
        request._cached_body = request.body  # cache before DRF consumes it

        start    = time.monotonic()
        response = self.get_response(request)
        elapsed  = time.monotonic() - start

        try:
            self._log(request, response, elapsed)
        except Exception:
            logger.error("RequestLoggerMiddleware failed to log", exc_info=True)

        return response

    def _log(self, request, response, elapsed: float) -> None:
        now         = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        ip          = get_client_ip(request)
        method      = request.method
        url         = request.get_full_path()
        status_code = getattr(response, "status_code", "N/A")
        msg         = _response_message(response)
        request_id  = getattr(request, "_request_id", "N/A")
        user_agent  = request.META.get("HTTP_USER_AGENT", "N/A")

        try:
            resp_headers = dict(response.items())
        except Exception:
            resp_headers = {}

        req_body = safe_request_body(request)

        try:
            req_size = _format_size(int(request.META.get("CONTENT_LENGTH") or 0))
        except (ValueError, TypeError):
            req_size = "N/A"

        try:
            resp_size = _format_size(int(resp_headers.get("Content-Length", 0)))
        except (ValueError, TypeError):
            resp_size = "N/A"

        block = "\n".join([
            BORDER,
            f"  REQUEST ID:   {request_id}",
            f"  TIME:         {now}",
            f"  IP:           {ip}",
            f"  {method}  {url}",
            f"  USER:         {_user_line(request)}",
            f"  DEVICE:       {user_agent}",
            "  " + "-" * 60,
            f"  REQ HEADERS:  {_headers_clean(request.headers)}",
            f"  REQ BODY:     {req_body if req_body else 'None'}",
            f"  REQ SIZE:     {req_size}",
            "  " + "-" * 60,
            f"  STATUS:       {status_code}",
            f"  MSG:          {msg if msg else '-'}",
            f"  RES HEADERS:  {resp_headers}",
            f"  RES SIZE:     {resp_size}",
            f"  EXEC TIME:    {elapsed:.4f}s",
            BORDER,
        ])

        if isinstance(status_code, int) and status_code >= 400:
            logger.warning(block)
        else:
            logger.info(block)