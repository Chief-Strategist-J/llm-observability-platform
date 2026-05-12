"""Main application entry point - OTEL tracer initialized FIRST."""

import os
import uvicorn
from fastapi import FastAPI

from .infra.tracing.tracer import initialize_tracer
from .api.rest.v1.router import create_app


def main():
    """Main entry point - initializes tracing before everything else."""
    # MUST initialize OTEL tracer FIRST
    initialize_tracer()
    
    # Create FastAPI application
    app = create_app()
    
    # Add tracing middleware after tracer initialization
    from .infra.tracing.middleware import TracingMiddleware
    app.add_middleware(TracingMiddleware)
    
    # Get configuration
    host = os.getenv('API_HOST', '0.0.0.0')
    port = int(os.getenv('API_PORT', '8000'))
    reload = os.getenv('API_RELOAD', 'false').lower() == 'true'
    
    # Run application
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        access_log=True
    )


if __name__ == "__main__":
    main()
