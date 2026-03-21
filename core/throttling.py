import logging
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

logger = logging.getLogger("api")


class _LoggedThrottleMixin:
    def allow_request(self, request, view):
        allowed = super().allow_request(request, view)
        if not allowed:
            user    = getattr(request, "user", None)
            user_id = getattr(user, "id", "anonymous") if user and user.is_authenticated else "anonymous"
            logger.warning(
                f"[THROTTLED] scope={getattr(self, 'scope', 'unknown')} "
                f"user_id={user_id} "
                f"endpoint={request.get_full_path()} "
                f"method={request.method}"
            )
        return allowed


class LoggedAnonRateThrottle(_LoggedThrottleMixin, AnonRateThrottle):
    scope = "anon"


class LoggedUserRateThrottle(_LoggedThrottleMixin, UserRateThrottle):
    scope = "user"