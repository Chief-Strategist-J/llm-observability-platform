import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
CONTRACT_FILE: Path = Path(
    os.getenv(
        "CONTRACTS_PATH",
        BASE_DIR / "contracts" / "events" / "llm_spans_raw.yaml",
    )
)

if not CONTRACT_FILE.exists():
    CONTRACT_FILE = Path("/app/contracts/events/llm_spans_raw.yaml")


def _extract_val(text: str, pattern: str) -> str:
    m = re.search(pattern, text, re.MULTILINE)
    if not m:
        raise ValueError(f"Missing expected pattern in contract: {pattern}")
    return m.group(1).strip()


def load_event_contract() -> dict:
    path = Path(CONTRACT_FILE)
    if not path.exists():
        raise ValueError(f"Contract file not found at {path}")
    text = path.read_text()
    _validate_event_contract(text)
    return {
        "event": "llm_spans_raw",
        "version": int(_extract_val(text, r"^version:\s*(\d+)\s*$")),
        "consumer_group": _extract_val(text, r"^consumer_group:\s*(\S+)\s*$"),
    }


def _validate_event_contract(text: str) -> None:
    required_fragments = [
        "llm.spans.raw",
        "consumeLlmSpansRaw",
        "span_id",
        "cost_usd_micro",
        "price_version",
        "consumer_group:",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            raise ValueError(f"Missing required contract fragment: {fragment}")

    version = int(_extract_val(text, r"^version:\s*(\d+)\s*$"))
    if version < 1:
        raise ValueError("Contract version must be positive integer")
