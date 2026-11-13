from contextvars import ContextVar
from uuid import uuid4


_audit_context = ContextVar("platform_audit_context", default={})

SENSITIVE_PARTS = (
    "password", "secret", "token", "authorization", "cookie", "credential",
    "recovery_code", "totp", "api_key", "access_key", "private_key",
)


def set_audit_context(*, request_id="", correlation_id=""):
    return _audit_context.set({
        "request_id": request_id[:100],
        "correlation_id": correlation_id[:100],
    })


def reset_audit_context(token):
    _audit_context.reset(token)


def current_audit_context():
    return _audit_context.get()


def request_audit_ids(request):
    request_id = request.headers.get("X-Request-ID", "").strip()[:100]
    correlation_id = request.headers.get("X-Correlation-ID", "").strip()[:100]
    return request_id, correlation_id or str(uuid4())


def sanitize_snapshot(value):
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if any(part in str(key).casefold() for part in SENSITIVE_PARTS)
            else sanitize_snapshot(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize_snapshot(item) for item in value]
    return value
