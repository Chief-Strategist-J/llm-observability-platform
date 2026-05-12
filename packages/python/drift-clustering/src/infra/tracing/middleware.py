"""Request-level observability middleware helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RequestContext:
    service: str
    endpoint: str
    user_id: str | None
    session_id: str | None


def build_request_context(
    *, service: str, endpoint: str, user_id: str | None, session_id: str | None
) -> RequestContext:
    return RequestContext(
        service=service,
        endpoint=endpoint,
        user_id=user_id,
        session_id=session_id,
    )
