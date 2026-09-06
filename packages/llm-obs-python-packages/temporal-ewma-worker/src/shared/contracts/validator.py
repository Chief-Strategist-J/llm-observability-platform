import os
import re
from pathlib import Path
from shared.errors.base import ValidationError

BASE_DIR = Path(__file__).resolve().parents[3]
CONTRACT_FILE: Path = Path(
    os.getenv(
        "CONTRACTS_PATH",
        BASE_DIR / "contracts" / "workflows" / "ewma_baseline_update.yaml",
    )
)

if not CONTRACT_FILE.exists():
    CONTRACT_FILE = Path("/app/contracts/workflows/ewma_baseline_update.yaml")


def _extract_val(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.MULTILINE)
    if not m:
        raise ValidationError(f"Missing expected pattern in contract: {pattern}")
    return m.group(1).strip()


def load_workflow_contract() -> dict:
    path = Path(CONTRACT_FILE)
    if not path.exists():
        raise ValidationError(f"Contract file not found at {path}")
    text = path.read_text()
    validate_workflow_contract(text)
    return {
        "workflow": "ewma_baseline_update",
        "version": int(_extract_val(text, r"^version:\s*(\d+)\s*$")),
        "cron": _extract_val(text, r"^schedule:\s*\n\s*cron:\s*\"(.*)\"\s*$"),
    }


def validate_workflow_contract(text: str) -> None:
    required_fragments = [
        "workflow: ewma_baseline_update",
        'cron: "0 * * * *"',
        "activities:",
        "fetch_active_pairs:",
        "upsert_baseline:",
        "publish_anomaly_alert:",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            raise ValidationError(f"Missing required contract fragment: {fragment}")

    version = int(_extract_val(text, r"^version:\s*(\d+)\s*$"))
    if version < 1:
        raise ValidationError("Contract version must be positive integer")
