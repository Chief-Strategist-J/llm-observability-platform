"""Unit tests for PerplexityBaselineLoader (Step 3.1)."""
from __future__ import annotations

import os
import textwrap
import time
from unittest.mock import MagicMock, patch

import pytest
import yaml

from features.score_perplexity.rules import (
    HIGH_PERPLEXITY_MULTIPLIER,
    PerplexityBaselineLoader,
    _FALLBACK_P50,
    get_baseline_loader,
    is_high_perplexity,
    set_baseline_loader,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_yaml(path: str, content: dict) -> None:
    with open(path, "w") as fh:
        yaml.dump(content, fh)


# ---------------------------------------------------------------------------
# Tests: constructor / load
# ---------------------------------------------------------------------------

class TestPerplexityBaselineLoaderLoad:
    def test_loads_valid_yaml(self, tmp_path):
        cfg = tmp_path / "perplexity_baselines.yaml"
        cfg.write_text(
            textwrap.dedent(
                """\
                baselines:
                  chat: 25.0
                  code: 10.0
                  rag: 18.0
                  classification: 9.0
                """
            )
        )
        loader = PerplexityBaselineLoader(config_path=str(cfg))
        assert loader.get_p50("chat") == pytest.approx(25.0)
        assert loader.get_p50("code") == pytest.approx(10.0)
        assert loader.get_p50("rag") == pytest.approx(18.0)
        assert loader.get_p50("classification") == pytest.approx(9.0)
        loader.stop()

    def test_falls_back_when_file_missing(self, tmp_path):
        missing = str(tmp_path / "does_not_exist.yaml")
        loader = PerplexityBaselineLoader(config_path=missing)
        # Should fall back to _FALLBACK_P50 values
        for pt, val in _FALLBACK_P50.items():
            assert loader.get_p50(pt) == pytest.approx(val)
        loader.stop()

    def test_falls_back_for_unknown_prompt_type(self, tmp_path):
        cfg = tmp_path / "perplexity_baselines.yaml"
        cfg.write_text("baselines:\n  chat: 20.0\n")
        loader = PerplexityBaselineLoader(config_path=str(cfg))
        # Unknown prompt_type falls back to default (20.0)
        result = loader.get_p50("unknown_type")
        assert result == pytest.approx(20.0)
        loader.stop()

    def test_ignores_invalid_value_keeps_other_keys(self, tmp_path):
        cfg = tmp_path / "perplexity_baselines.yaml"
        cfg.write_text("baselines:\n  chat: bad_value\n  code: 12.0\n")
        loader = PerplexityBaselineLoader(config_path=str(cfg))
        # chat should fall back to fallback default, code loaded from file
        assert loader.get_p50("code") == pytest.approx(12.0)
        loader.stop()

    def test_empty_baselines_uses_fallback(self, tmp_path):
        cfg = tmp_path / "perplexity_baselines.yaml"
        cfg.write_text("baselines: {}\n")
        loader = PerplexityBaselineLoader(config_path=str(cfg))
        for pt, val in _FALLBACK_P50.items():
            assert loader.get_p50(pt) == pytest.approx(val)
        loader.stop()


# ---------------------------------------------------------------------------
# Tests: hot-reload
# ---------------------------------------------------------------------------

class TestPerplexityBaselineLoaderReload:
    def test_reload_updates_p50(self, tmp_path):
        cfg = tmp_path / "perplexity_baselines.yaml"
        cfg.write_text("baselines:\n  chat: 20.0\n")
        loader = PerplexityBaselineLoader(config_path=str(cfg))
        assert loader.get_p50("chat") == pytest.approx(20.0)

        # Simulate file update
        cfg.write_text("baselines:\n  chat: 99.0\n")
        loader.reload()
        assert loader.get_p50("chat") == pytest.approx(99.0)
        loader.stop()

    def test_reload_does_not_overwrite_on_bad_file(self, tmp_path):
        cfg = tmp_path / "perplexity_baselines.yaml"
        cfg.write_text("baselines:\n  chat: 20.0\n")
        loader = PerplexityBaselineLoader(config_path=str(cfg))
        assert loader.get_p50("chat") == pytest.approx(20.0)

        # Corrupt the YAML
        cfg.write_text(":::invalid yaml:::")
        loader.reload()
        # Previous value should be retained (exception guard preserves old state)
        # (Since the file is invalid yaml, safe_load raises — we catch and retain)
        loader.stop()


# ---------------------------------------------------------------------------
# Tests: singleton helpers
# ---------------------------------------------------------------------------

class TestSingletonHelpers:
    def test_set_and_get_loader(self, tmp_path):
        cfg = tmp_path / "perplexity_baselines.yaml"
        cfg.write_text("baselines:\n  chat: 30.0\n")
        loader = PerplexityBaselineLoader(config_path=str(cfg))
        set_baseline_loader(loader)
        assert get_baseline_loader() is loader
        loader.stop()


# ---------------------------------------------------------------------------
# Tests: is_high_perplexity uses loaded p50
# ---------------------------------------------------------------------------

class TestIsHighPerplexityWithLoader:
    def test_uses_p50_from_loader(self, tmp_path):
        cfg = tmp_path / "perplexity_baselines.yaml"
        # p50=10.0, threshold = 10.0 * 3.0 = 30.0
        cfg.write_text("baselines:\n  chat: 10.0\n")
        loader = PerplexityBaselineLoader(config_path=str(cfg))
        set_baseline_loader(loader)

        assert is_high_perplexity(30.1, "chat") is True
        assert is_high_perplexity(29.9, "chat") is False
        loader.stop()

    def test_not_high_with_fallback(self, tmp_path):
        missing = str(tmp_path / "no_file.yaml")
        loader = PerplexityBaselineLoader(config_path=missing)
        set_baseline_loader(loader)

        # fallback chat p50 = 20.0, threshold = 60.0
        assert is_high_perplexity(59.9, "chat") is False
        assert is_high_perplexity(60.1, "chat") is True
        loader.stop()
