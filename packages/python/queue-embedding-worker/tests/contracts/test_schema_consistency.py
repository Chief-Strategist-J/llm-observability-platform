from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
YAML_CONTRACT = ROOT / "contracts" / "jobs" / "enrich-span.yaml"
PROTO_CONTRACT = ROOT / "contracts" / "proto" / "enrich_span.proto"
GRAPHQL_SCHEMA = ROOT / "contracts" / "graphql" / "schema.graphql"
OPENAPI_SCHEMA = ROOT / "contracts" / "api.yaml"


def _yaml_required_fields(text: str) -> set[str]:
    m = re.search(r"required:\s*\[([^\]]+)\]", text)
    assert m, "required fields not found in yaml"
    return {part.strip() for part in m.group(1).split(",")}


def _proto_request_fields(text: str) -> set[str]:
    block = re.search(r"message\s+EnrichSpanRequest\s*\{([^}]+)\}", text, re.S)
    assert block, "EnrichSpanRequest not found"
    fields = re.findall(r"\s+\w+\s+(\w+)\s*=\s*\d+;", block.group(1))
    return set(fields)


def _graphql_input_fields(text: str) -> set[str]:
    block = re.search(r"input\s+EnrichSpanInput\s*\{([^}]+)\}", text, re.S)
    assert block, "EnrichSpanInput not found"
    fields = re.findall(r"\s*(\w+)\s*:\s*\w+!", block.group(1))
    return set(fields)


def _snake_to_camel(name: str) -> str:
    head, *tail = name.split("_")
    return head + "".join(x.title() for x in tail)


def test_payload_fields_match_across_yaml_proto_graphql():
    yaml_fields = _yaml_required_fields(YAML_CONTRACT.read_text())
    proto_fields = _proto_request_fields(PROTO_CONTRACT.read_text())
    graphql_fields = _graphql_input_fields(GRAPHQL_SCHEMA.read_text())

    assert proto_fields == yaml_fields
    assert graphql_fields == {_snake_to_camel(f) for f in yaml_fields}


def test_result_embedding_key_pattern_matches_contract_intent():
    yaml_text = YAML_CONTRACT.read_text()
    assert "pattern: '^emb_[a-f0-9]{24}$'" in yaml_text


def test_openapi_contains_execute_and_health_paths():
    text = OPENAPI_SCHEMA.read_text()
    assert "/health:" in text
    assert "/execute/{jobName}:" in text
