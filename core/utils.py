import json


def get_client_ip(request) -> str:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def mask_phone(phone: str) -> str:
    if not phone:
        return "N/A"
    phone = str(phone)
    if len(phone) <= 5:
        return "*" * len(phone)
    return phone[:3] + "*" * (len(phone) - 5) + phone[-2:]


def mask_token(token: str) -> str:
    if not token:
        return "N/A"
    token = str(token)
    if token.lower().startswith("bearer "):
        token = token[7:]
    if len(token) <= 14:
        return "***"
    return token[:10] + "..." + token[-4:]


def safe_request_body(request) -> dict:
    _SENSITIVE = {
        "password", "old_password", "new_password", "confirm_password",
        "confirm_new_password", "token", "access_token", "refresh_token",
        "secret", "api_key", "authorization", "credit_card", "cvv", "ssn",
    }
    body: dict = {}
    try:
        # Use _cached_body set by middleware before DRF consumes request.body
        raw_bytes = getattr(request, "_cached_body", None) or request.body
        if not raw_bytes:
            return {}
        raw = json.loads(raw_bytes.decode("utf-8"))
        for key, value in raw.items():
            if key.lower() in _SENSITIVE:
                body[key] = "***REDACTED***"
            elif isinstance(value, list) and len(value) == 1:
                body[key] = value[0]
            else:
                body[key] = value
    except Exception:
        pass
    return body