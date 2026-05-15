from pathlib import Path
import re

CONTRACT_FILE = Path(__file__).resolve().parents[3] / "contracts" / "jobs" / "enrich-span.yaml"


class ContractValidationError(ValueError):
    pass


def _extract_int(text: str, key: str) -> int:
    m = re.search(rf"^{key}:\s*(\d+)\s*$", text, re.MULTILINE)
    if not m:
        raise ContractValidationError(f"Missing integer key: {key}")
    return int(m.group(1))


def load_enrich_span_contract() -> dict:
    text = CONTRACT_FILE.read_text()
    validate_enrich_span_contract(text)
    return {"job": "enrich-span", "version": _extract_int(text, "version")}


def validate_enrich_span_contract(text: str) -> None:
    required_lines = [
        "job: enrich-span",
        "queue: span-enrichment",
        "timeout_seconds:",
        "retry:",
        "max_attempts:",
        "backoff_ms:",
        "payload:",
        "result:",
        "required: [trace_id, span_id, model, text]",
        "pattern: '^emb_[a-f0-9]{24}$'",
    ]
    for line in required_lines:
        if line not in text:
            raise ContractValidationError(f"Missing required contract fragment: {line}")

    if _extract_int(text, "version") < 1:
        raise ContractValidationError("version must be positive integer")
    if _extract_int(text, "timeout_seconds") <= 0:
        raise ContractValidationError("timeout_seconds must be > 0")
