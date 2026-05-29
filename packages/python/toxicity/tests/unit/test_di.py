from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch
import pytest

from shared.di.providers import build_toxicity_scorer, build_toxicity_publisher
from api.rest.v1.app import create_app

def test_build_toxicity_scorer():
    with patch("infra.adapters.detoxify_onnx_adapter.DetoxifyOnnxAdapter") as mock_adapter:
        scorer = build_toxicity_scorer()
        assert scorer is not None

def test_build_toxicity_publisher():
    publisher = build_toxicity_publisher()
    assert publisher is not None

def test_create_app():
    with patch("api.rest.v1.app.build_toxicity_scorer") as mock_scorer, \
         patch("api.rest.v1.app.build_toxicity_publisher") as mock_pub:
        app = create_app()
        assert app is not None
        assert hasattr(app.state, "toxicity_scorer")
        assert hasattr(app.state, "toxicity_publisher")
