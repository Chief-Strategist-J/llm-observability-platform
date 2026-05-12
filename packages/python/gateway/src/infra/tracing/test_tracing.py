from infra.tracing.middleware import build_request_context
from infra.tracing.tracer import start_span_timer


def test_span_timer_tracks_elapsed_time() -> None:
    timer = start_span_timer()
    timer.mark_first_token()
    assert timer.ttft_ms() >= 0
    assert timer.total_ms() >= 0


def test_request_context_builder() -> None:
    ctx = build_request_context(
        service="gateway", endpoint="/v1/chat", user_id="u1", session_id="s1"
    )
    assert ctx.service == "gateway"
    assert ctx.endpoint == "/v1/chat"
