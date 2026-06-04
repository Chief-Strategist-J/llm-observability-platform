import os
import re
from pathlib import Path
from shared.errors.base import ValidationError

BASE_DIR = Path(__file__).resolve().parents[3]
RECOMPUTE_CONTRACT: Path = BASE_DIR / "contracts" / "workflows" / "recompute_quality_baseline.yaml"
ROLLUP_CONTRACT: Path = BASE_DIR / "contracts" / "workflows" / "rollup_quality_trend.yaml"

def _extract_val(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.MULTILINE)
    if not m:
        raise ValidationError(f"Missing expected pattern in contract: {pattern}")
    return m.group(1).strip()


def load_workflow_contracts() -> dict:
    if not RECOMPUTE_CONTRACT.exists():
        raise ValidationError(f"Contract file not found at {RECOMPUTE_CONTRACT}")
    if not ROLLUP_CONTRACT.exists():
        raise ValidationError(f"Contract file not found at {ROLLUP_CONTRACT}")

    recompute_text = RECOMPUTE_CONTRACT.read_text()
    rollup_text = ROLLUP_CONTRACT.read_text()

    validate_recompute_contract(recompute_text)
    validate_rollup_contract(rollup_text)

    return {
        "recompute": {
            "workflow": "recompute_quality_baseline",
            "version": int(_extract_val(recompute_text, r"^version:\s*(\d+)\s*$")),
            "cron": _extract_val(recompute_text, r"^schedule:\s*\n\s*cron:\s*\"(.*)\"\s*$"),
        },
        "rollup": {
            "workflow": "rollup_quality_trend",
            "version": int(_extract_val(rollup_text, r"^version:\s*(\d+)\s*$")),
            "cron": _extract_val(rollup_text, r"^schedule:\s*\n\s*cron:\s*\"(.*)\"\s*$"),
        }
    }


def validate_recompute_contract(text: str) -> None:
    required_fragments = [
        "workflow: recompute_quality_baseline",
        'cron: "0 * * * *"',
        "activities:",
        "recompute_baseline_scores:",
        "write_redis_baselines:",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            raise ValidationError(f"Missing required contract fragment: {fragment}")

    version = int(_extract_val(text, r"^version:\s*(\d+)\s*$"))
    if version < 1:
        raise ValidationError("Contract version must be positive integer")


def validate_rollup_contract(text: str) -> None:
    required_fragments = [
        "workflow: rollup_quality_trend",
        'cron: "0 0 * * *"',
        "activities:",
        "rollup_quality_trend:",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            raise ValidationError(f"Missing required contract fragment: {fragment}")

    version = int(_extract_val(text, r"^version:\s*(\d+)\s*$"))
    if version < 1:
        raise ValidationError("Contract version must be positive integer")
