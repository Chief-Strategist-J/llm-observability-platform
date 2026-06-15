#!/usr/bin/env python3
"""
seed_baselines.py — Compute p50 perplexity baselines per prompt_type
and write them to perplexity_baselines.yaml.

Usage:
    python scripts/seed_baselines.py [--output PATH] [--sample-count N]

Environment:
    PERPLEXITY_SERVICE_URL  Base URL of the perplexity worker (default: http://localhost:8008)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import string
import urllib.error
import urllib.request
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_baselines")

# Prompt types to compute baselines for
PROMPT_TYPES: list[str] = ["chat", "code", "rag", "classification"]

# Hardcoded fallback p50 values used when the perplexity worker is unavailable
_FALLBACK_P50: dict[str, float] = {
    "chat": 20.0,
    "code": 12.0,
    "rag": 16.0,
    "classification": 8.0,
}

# Word pools for synthetic response generation per prompt_type
_WORD_POOL: dict[str, list[str]] = {
    "chat": [
        "hello", "world", "how", "are", "you", "doing", "today", "great",
        "fine", "thanks", "what", "is", "the", "weather", "like", "nice",
        "good", "morning", "evening", "please", "help", "me", "understand",
        "this", "topic", "explain", "simply", "sure", "absolutely",
    ],
    "code": [
        "def", "function", "return", "class", "import", "module", "variable",
        "loop", "for", "while", "if", "else", "try", "except", "yield",
        "async", "await", "lambda", "print", "list", "dict", "set", "tuple",
        "index", "range", "enumerate", "append", "extend", "pop",
    ],
    "rag": [
        "according", "to", "the", "document", "source", "retrieved", "context",
        "passage", "states", "that", "based", "on", "information", "provided",
        "relevant", "content", "mentions", "found", "in", "reference", "text",
        "above", "below", "paragraph", "section", "article", "data", "evidence",
    ],
    "classification": [
        "positive", "negative", "neutral", "sentiment", "label", "category",
        "class", "spam", "ham", "toxic", "safe", "urgent", "normal", "high",
        "low", "medium", "critical", "benign", "malicious", "flagged",
        "approved", "rejected", "pending", "complete", "incomplete",
    ],
}


def _generate_response(prompt_type: str, word_count: int = 30) -> str:
    """Generate a synthetic response text of ~word_count words for a given prompt_type."""
    words = _WORD_POOL.get(prompt_type, _WORD_POOL["chat"])
    chosen = [random.choice(words) for _ in range(word_count)]
    return " ".join(chosen) + "."


def _call_perplexity_worker(
    base_url: str,
    response_text: str,
    prompt_type: str,
    completion_tokens: int = 50,
    timeout_seconds: int = 10,
) -> float | None:
    """POST /v1/score/perplexity and return the perplexity value or None on failure."""
    url = f"{base_url.rstrip('/')}/v1/score/perplexity"
    body = json.dumps(
        {
            "response_text": response_text,
            "completion_tokens": completion_tokens,
            "prompt_type": prompt_type,
        }
    ).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            data = json.loads(resp.read())
            value = data.get("perplexity") or data.get("perplexity_score")
            if value is not None:
                return float(value)
            logger.warning("No 'perplexity' field in response: %s", data)
            return None
    except (urllib.error.URLError, json.JSONDecodeError, ValueError, TimeoutError) as exc:
        logger.debug("Worker call failed: %s", exc)
        return None


def _p50(values: list[float]) -> float:
    """Compute the 50th percentile (median) of a sorted list — no numpy required."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 1:
        return sorted_vals[mid]
    return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0


def compute_baselines(
    service_url: str,
    sample_count: int,
) -> dict[str, float]:
    """For each prompt_type, collect perplexity samples and return p50 per type."""
    baselines: dict[str, float] = {}

    for pt in PROMPT_TYPES:
        logger.info("Computing baseline for prompt_type=%s (samples=%d)...", pt, sample_count)
        values: list[float] = []

        for i in range(sample_count):
            text = _generate_response(pt)
            ppl = _call_perplexity_worker(service_url, text, pt)
            if ppl is not None:
                values.append(ppl)
            if (i + 1) % 50 == 0:
                logger.info("  prompt_type=%s: %d/%d samples collected", pt, len(values), i + 1)

        if values:
            p50_val = _p50(values)
            logger.info(
                "  prompt_type=%s: p50=%.4f (from %d valid samples)", pt, p50_val, len(values)
            )
            baselines[pt] = round(p50_val, 4)
        else:
            fallback = _FALLBACK_P50[pt]
            logger.warning(
                "  prompt_type=%s: worker unavailable — using fallback p50=%.4f",
                pt, fallback,
            )
            baselines[pt] = fallback

    return baselines


def write_yaml(baselines: dict[str, float], output_path: Path) -> None:
    """Write baselines dict to YAML at output_path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "# Generated by seed_baselines.py — do not edit manually": None,
        "baselines": baselines,
    }
    # Build clean YAML manually to preserve comment
    lines = [
        "# Perplexity baselines: p50 values per prompt_type.",
        "# Generated by seed_baselines.py; hot-reloaded on change by PerplexityBaselineLoader.",
        "# HIGH_PERPLEXITY threshold = p50 * HIGH_PERPLEXITY_MULTIPLIER (3.0)",
        "baselines:",
    ]
    for pt in PROMPT_TYPES:
        lines.append(f"  {pt}: {baselines[pt]}")
    lines.append("")
    output_path.write_text("\n".join(lines))
    logger.info("Baselines written to %s", output_path)


def _default_output_path() -> Path:
    """Resolve the perplexity package root and return path to perplexity_baselines.yaml."""
    # scripts/ is one level below the package root
    here = Path(__file__).resolve().parent
    return here.parent / "perplexity_baselines.yaml"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed perplexity p50 baselines by sampling the perplexity worker."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_default_output_path(),
        help="Output YAML path (default: perplexity_baselines.yaml in package root)",
    )
    parser.add_argument(
        "--sample-count",
        type=int,
        default=500,
        help="Number of synthetic samples per prompt_type (default: 500)",
    )
    args = parser.parse_args()

    service_url = os.environ.get("PERPLEXITY_SERVICE_URL", "http://localhost:8008")
    logger.info(
        "Starting baseline seeding: service=%s samples=%d output=%s",
        service_url, args.sample_count, args.output,
    )

    baselines = compute_baselines(service_url=service_url, sample_count=args.sample_count)
    write_yaml(baselines, args.output)

    logger.info("Done. Baselines: %s", baselines)


if __name__ == "__main__":
    main()
