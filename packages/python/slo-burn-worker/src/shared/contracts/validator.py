import os
import re
from pathlib import Path
from typing import Any
from shared.errors.base import ValidationError

BASE_DIR = Path(__file__).resolve().parents[3]
CONTRACT_FILE: Path = Path(
    os.getenv(
        "CONTRACTS_PATH",
        BASE_DIR / "contracts" / "workflows" / "slo_burn_computation.yaml",
    )
)

if not CONTRACT_FILE.exists():
    CONTRACT_FILE = Path("/app/contracts/workflows/slo_burn_computation.yaml")


def _extract_val(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.MULTILINE)
    if not m:
        raise ValidationError(f"Missing expected pattern in contract: {pattern}")
    return m.group(1).strip()


def load_workflow_contract() -> dict[str, Any]:
    path = Path(CONTRACT_FILE)
    if not path.exists():
        raise ValidationError(f"Contract file not found at {path}")
    text = path.read_text()
    validate_workflow_contract(text)
    return {
        "workflow": "slo_burn_computation",
        "version": int(_extract_val(text, r"^version:\s*(\d+)\s*$")),
        "cron": _extract_val(text, r"^schedule:\s*\n\s*cron:\s*\"(.*)\"\s*$"),
    }


def validate_workflow_contract(text: str) -> None:
    required_fragments = [
        "workflow: slo_burn_computation",
        'cron: "* * * * *"',
        "activities:",
        "fetch_active_pairs:",
        "compute_burn_rates:",
        "write_burn_rates:",
        "handle_alerts:",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            raise ValidationError(f"Missing required contract fragment: {fragment}")

    version = int(_extract_val(text, r"^version:\s*(\d+)\s*$"))
    if version < 1:
        raise ValidationError("Contract version must be positive integer")
