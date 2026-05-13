import json
import sys
import os
from typing import Any, Dict

# Add src to path so we can import the model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

try:
    from features.spans.types import LLMSpan
except ImportError as e:
    print(f"Error: Could not import LLMSpan from features.spans.types. {e}")
    sys.exit(1)

CONTRACT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../contracts/asyncapi/schemas/span.json"))

def resolve_schema(schema: Any, definitions: Dict[str, Any]) -> Any:
    """Simplifies Pydantic schema by resolving $refs and anyOf [type, null]."""
    if not isinstance(schema, dict):
        return schema
    
    if "$ref" in schema:
        ref_path = schema["$ref"].split("/")[-1]
        return resolve_schema(definitions.get(ref_path, {}), definitions)
    
    if "anyOf" in schema:
        types = []
        non_null_branch = None
        for s in schema["anyOf"]:
            resolved = resolve_schema(s, definitions)
            if isinstance(resolved, dict):
                t = resolved.get("type")
                if isinstance(t, list):
                    types.extend(t)
                elif t:
                    types.append(t)
                
                if t != "null":
                    non_null_branch = resolved
        
        # If we have a non-null branch, merge its constraints into a combined schema
        if non_null_branch:
            result = non_null_branch.copy()
            if "null" in types:
                if isinstance(result.get("type"), list):
                    if "null" not in result["type"]:
                        result["type"].append("null")
                else:
                    result["type"] = [result["type"], "null"]
            return result
                
    return schema

def deep_compare(path: str, source: Any, target: Any) -> list[str]:
    errors = []
    
    # Handle the case where one side is a single type and the other is a list [type, "null"]
    s_type = source.get("type") if isinstance(source, dict) else None
    t_type = target.get("type") if isinstance(target, dict) else None
    
    if s_type and t_type:
        s_types = set(s_type) if isinstance(s_type, list) else {s_type}
        t_types = set(t_type) if isinstance(t_type, list) else {t_type}
        if s_types != t_types:
            errors.append(f"Type mismatch at {path}: source={s_types}, target={t_types}")

    # Check Enum
    if isinstance(source, dict) and "enum" in source and isinstance(target, dict) and "enum" in target:
        if set(source["enum"]) != set(target["enum"]):
            errors.append(f"Enum mismatch at {path}: source={source['enum']}, target={target['enum']}")

    # Check numeric and string/array constraints
    for constraint in ["minimum", "exclusiveMinimum", "maximum", "exclusiveMaximum", "minLength", "maxLength", "minItems", "maxItems"]:
        if isinstance(target, dict) and constraint in target:
            if isinstance(source, dict) and constraint in source:
                if source[constraint] != target[constraint]:
                    errors.append(f"Constraint mismatch at {path}.{constraint}: source={source[constraint]}, target={target[constraint]}")
            else:
                errors.append(f"Missing constraint in implementation at {path}.{constraint}")

    # Recursive check for properties
    if isinstance(target, dict) and "properties" in target:
        source_props = source.get("properties", {})
        for key, t_prop in target["properties"].items():
            if key not in source_props:
                errors.append(f"Missing property in implementation: {path}.{key}")
            else:
                errors.extend(deep_compare(f"{path}.{key}", source_props[key], t_prop))

    return errors

def main():
    if not os.path.exists(CONTRACT_PATH):
        print(f"Error: Contract file not found at {CONTRACT_PATH}")
        sys.exit(1)

    with open(CONTRACT_PATH, "r") as f:
        contract_schema = json.load(f)

    # Generate Pydantic schema
    raw_impl_schema = LLMSpan.model_json_schema()
    definitions = raw_impl_schema.get("$defs", {})
    
    # Resolve all implementation properties
    impl_properties = {}
    for key, prop in raw_impl_schema.get("properties", {}).items():
        if key == "span_warnings": continue
        impl_properties[key] = resolve_schema(prop, definitions)
    
    impl_schema = {"properties": impl_properties, "required": raw_impl_schema.get("required", [])}

    # Compare
    errors = []
    errors.extend(deep_compare("root", impl_schema, contract_schema))
    
    # Check for all fields in contract being present
    contract_required = set(contract_schema.get("required", []))
    impl_all_fields = set(impl_properties.keys())
    
    missing_fields = contract_required - impl_all_fields
    if missing_fields:
        errors.append(f"Implementation is missing required fields from contract: {missing_fields}")

    if errors:
        print("❌ Contract Violation Detected!")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("✅ Implementation matches contract perfectly.")
        sys.exit(0)

if __name__ == "__main__":
    main()
