from __future__ import annotations

import pytest

def test_app_initialization_with_discovery():
    from api.rest.v1.app import create_app
    app = create_app()
    assert app.title == "NLI Worker"
    assert app.version == "0.1.0"
