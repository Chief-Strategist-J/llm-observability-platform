import pytest
from pytrace_features.diff.service import DiffService

def test_diff_service_renders(capsys):
    service = DiffService()
    service.compare("v1.2", "v1.3")
    captured = capsys.readouterr()
    assert "REGRESSIONS" in captured.out
    assert "NEW CALLS in v1.3" in captured.out
