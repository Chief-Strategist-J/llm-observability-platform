from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from .tracer import init_tracer
import os

from typing import Optional, Any

def instrument_app(app, tracer_provider: Optional[Any] = None):
    if tracer_provider is None:
        init_tracer("instrumentation-sdk-api", os.getenv("DEPLOYMENT_ENV", "dev"))
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

