"""
tracep
======
A fire-and-forget OpenTelemetry tracer SDK.

Public surface
--------------
- :class:`Tracer`    — main facade class
- :class:`WithParent` — typed str helper for the ``parent`` kwarg
- :class:`WithLevel`  — typed str helper for the ``level`` kwarg

Quick start::

    from tracep import Tracer

    tracer = Tracer("http://localhost:4318", "my-api-key", "my-service")
    tid = tracer.start("my-operation")
    tracer.trace(tid, "MyClass", "my_function", "step1", "doing work")
    tracer.end(tid, "ok")
"""

from .tracer import Tracer, WithLevel, WithParent

__all__ = ["Tracer", "WithParent", "WithLevel"]
