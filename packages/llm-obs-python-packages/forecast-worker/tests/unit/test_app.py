from __future__ import annotations

import pytest

def test_forecast_app_initialization_with_discovery():
    from api.rest.v1.app import create_app
    app = create_app()
    assert app.title == "Temporal Forecast Worker API"
    assert app.version == "1.0.0"
