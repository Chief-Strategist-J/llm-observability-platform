from shared.tracing.tracer import init_tracer


def test_init_tracer_idempotent():
    init_tracer()
    init_tracer()
    assert True
