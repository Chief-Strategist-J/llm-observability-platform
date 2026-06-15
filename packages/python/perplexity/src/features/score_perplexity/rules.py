from __future__ import annotations

import logging
import math
import os
import threading
from typing import Any

import yaml
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

from features.score_perplexity.types import PerplexityInput, PromptType

logger = logging.getLogger(__name__)

MIN_COMPLETION_TOKENS: int = 10
HIGH_PERPLEXITY_MULTIPLIER: float = 3.0
WEIGHT_ACTIVE: float = 0.10
WEIGHT_SKIPPED: float = 0.00
BLOCKED_FINISH_REASONS: frozenset[str] = frozenset({"content_filter"})

# Fallback hardcoded baselines (baseline_low, baseline_high) per prompt_type
_BASELINES: dict[PromptType, tuple[float, float]] = {
    "chat": (15.0, 35.0),
    "code": (8.0, 20.0),
    "rag": (12.0, 28.0),
    "classification": (6.0, 15.0),
}

# Default p50 values matching the YAML seeded values
_FALLBACK_P50: dict[PromptType, float] = {
    "chat": 20.0,
    "code": 12.0,
    "rag": 16.0,
    "classification": 8.0,
}


class _BaselineFileHandler(FileSystemEventHandler):
    """Watchdog handler that triggers a reload when perplexity_baselines.yaml changes."""

    def __init__(self, loader: "PerplexityBaselineLoader") -> None:
        super().__init__()
        self._loader = loader

    def on_modified(self, event: Any) -> None:  # type: ignore[override]
        if os.path.basename(event.src_path) == "perplexity_baselines.yaml":
            logger.info("perplexity_baselines.yaml changed — hot-reloading")
            self._loader.reload()


class PerplexityBaselineLoader:
    """
    Loads p50 perplexity baselines from perplexity_baselines.yaml at startup.
    Falls back to _FALLBACK_P50 if file is absent or malformed.
    Hot-reloads on file changes using watchdog (inotify with PollingObserver fallback).
    Thread-safe: reads protected by a RLock.
    """

    def __init__(self, config_path: str | None = None) -> None:
        self._lock = threading.RLock()
        self._config_path = config_path or self._default_path()
        self._p50: dict[str, float] = {}
        self.reload()
        self._observer: Observer | PollingObserver | None = self._start_watcher()

    @staticmethod
    def _default_path() -> str:
        # Walk up from this file to the package root and find perplexity_baselines.yaml
        here = os.path.dirname(os.path.abspath(__file__))
        # src/features/score_perplexity -> up 3 levels -> package root
        package_root = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
        return os.path.join(package_root, "perplexity_baselines.yaml")

    def reload(self) -> None:
        """Read the YAML file and update in-memory p50 dict; fall back if unavailable."""
        loaded: dict[str, float] = {}
        try:
            with open(self._config_path, "r") as fh:
                data = yaml.safe_load(fh)
            if isinstance(data, dict) and isinstance(data.get("baselines"), dict):
                for pt, val in data["baselines"].items():
                    try:
                        loaded[pt] = float(val)
                    except (TypeError, ValueError):
                        logger.warning("Invalid p50 for prompt_type=%s value=%s — skipped", pt, val)
        except FileNotFoundError:
            logger.warning(
                "perplexity_baselines.yaml not found at %s — using hardcoded fallback",
                self._config_path,
            )
        except Exception as exc:
            logger.error("Failed to load perplexity_baselines.yaml: %s — using current values", exc)
            return  # keep previous valid values

        with self._lock:
            self._p50 = loaded if loaded else dict(_FALLBACK_P50)
        logger.info("Perplexity baselines reloaded: %s", self._p50)

    def get_p50(self, prompt_type: str) -> float:
        """Return p50 baseline for the given prompt_type; uses fallback if not found."""
        with self._lock:
            return self._p50.get(prompt_type, _FALLBACK_P50.get(prompt_type, 20.0))  # type: ignore[return-value]

    def _start_watcher(self) -> Observer | PollingObserver | None:
        dir_to_watch = os.path.dirname(self._config_path)
        if not os.path.isdir(dir_to_watch):
            return None
        handler = _BaselineFileHandler(self)
        for observer_cls in (Observer, PollingObserver):
            try:
                obs = observer_cls()  # type: ignore[call-arg]
                obs.schedule(handler, path=dir_to_watch, recursive=False)
                obs.start()
                logger.info(
                    "Watchdog observer started (%s) on %s",
                    observer_cls.__name__,
                    dir_to_watch,
                )
                return obs
            except Exception as exc:
                logger.debug("Could not start %s: %s", observer_cls.__name__, exc)
        logger.warning("Could not start any watchdog observer — hot-reload disabled")
        return None

    def stop(self) -> None:
        """Gracefully stop the watchdog observer (call on app shutdown)."""
        if self._observer is not None:
            try:
                self._observer.stop()
                self._observer.join(timeout=5)
            except Exception:
                pass


# Module-level singleton — replaced by the app startup lifecycle
_baseline_loader: PerplexityBaselineLoader | None = None


def get_baseline_loader() -> PerplexityBaselineLoader:
    """Return the module-level singleton loader (initialized at app startup)."""
    global _baseline_loader
    if _baseline_loader is None:
        _baseline_loader = PerplexityBaselineLoader()
    return _baseline_loader


def set_baseline_loader(loader: PerplexityBaselineLoader) -> None:
    """Replace the module-level singleton (used by tests and app startup)."""
    global _baseline_loader
    _baseline_loader = loader


def baseline_for(prompt_type: PromptType) -> tuple[float, float]:
    return _BASELINES[prompt_type]


def should_skip(input: PerplexityInput) -> tuple[bool, str | None]:
    if input.finish_reason in BLOCKED_FINISH_REASONS:
        return True, "finish_reason_blocked"
    if input.completion_tokens < MIN_COMPLETION_TOKENS:
        return True, "completion_tokens_too_few"
    return False, None


def compute_perplexity_from_logprobs(token_logprobs: list[float]) -> float:
    n = len(token_logprobs)
    return math.exp(-sum(token_logprobs) / n)


def is_high_perplexity(perplexity: float, prompt_type: PromptType) -> bool:
    """Return True when perplexity > HIGH_PERPLEXITY_MULTIPLIER × p50 baseline."""
    p50 = get_baseline_loader().get_p50(prompt_type)
    return perplexity > HIGH_PERPLEXITY_MULTIPLIER * p50


def normalize_contribution(perplexity: float, prompt_type: PromptType) -> float:
    baseline_low, baseline_high = baseline_for(prompt_type)
    log_perp = math.log(max(perplexity, 1.0))
    log_low = math.log(max(baseline_low, 1.0))
    log_high = math.log(max(baseline_high, 1.0))
    raw = 1.0 / log_perp if log_perp > 0 else 0.0
    high_contrib = 1.0 / log_low if log_low > 0 else 1.0
    low_contrib = 1.0 / log_high if log_high > 0 else 0.0
    rng = high_contrib - low_contrib
    if rng <= 0:
        return 0.0
    normalized = (raw - low_contrib) / rng
    return max(0.0, min(1.0, normalized))
