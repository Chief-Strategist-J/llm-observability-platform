import pytest
from pytrace_features.stitch.service import StitchService

def test_stitch_service_renders(capsys):
    service = StitchService()
    service.stitch_traces(["api", "worker"])
    captured = capsys.readouterr()
    assert "REQUEST trace-id" in captured.out
    assert "api-service" in captured.out
