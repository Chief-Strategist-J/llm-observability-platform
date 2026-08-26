from typing import Any, Dict, List, TypedDict, Callable

class MapOp(TypedDict, total=False):
    op: str  # "rename" | "pick" | "omit" | "coerce" | "default"
    from_key: str
    to_key: str
    keys: List[str]
    target_type: str  # "int" | "float" | "str" | "bool"
    key: str
    value: Any

TYPE_CONVERTERS: Dict[str, Callable[[Any], Any]] = {
    "int": lambda v: int(v),
    "float": lambda v: float(v),
    "str": lambda v: str(v),
    "bool": lambda v: bool(v),
}

def _op_rename(result: Dict[str, Any], op: MapOp) -> Dict[str, Any]:
    from_k = op.get("from_key")
    to_k = op.get("to_key")
    has_keys = bool(from_k and to_k and from_k in result)
    return {**result, to_k: result.get(from_k)} if has_keys else result

def _op_pick(result: Dict[str, Any], op: MapOp) -> Dict[str, Any]:
    keys = set(op.get("keys", []))
    return {k: v for k, v in result.items() if k in keys}

def _op_omit(result: Dict[str, Any], op: MapOp) -> Dict[str, Any]:
    keys = set(op.get("keys", []))
    return {k: v for k, v in result.items() if k not in keys}

def _op_coerce(result: Dict[str, Any], op: MapOp) -> Dict[str, Any]:
    key = op.get("key")
    target_type = op.get("target_type")
    converter = TYPE_CONVERTERS.get(target_type, lambda v: v)
    should_coerce = bool(key and key in result and result[key] is not None)
    return {**result, key: converter(result[key])} if should_coerce else result

def _op_default(result: Dict[str, Any], op: MapOp) -> Dict[str, Any]:
    key = op.get("key")
    default_val = op.get("value")
    should_apply = bool(key and (key not in result or result[key] is None))
    return {**result, key: default_val} if should_apply else result

OP_TRANSFORMERS: Dict[str, Callable[[Dict[str, Any], MapOp], Dict[str, Any]]] = {
    "rename": _op_rename,
    "pick": _op_pick,
    "omit": _op_omit,
    "coerce": _op_coerce,
    "default": _op_default,
}

def map_json(data: Dict[str, Any], ops: List[MapOp]) -> Dict[str, Any]:
    """
    Pure Data-Driven Anti-Corruption Layer Mapper without if/else branching.
    """
    def _apply_op(current: Dict[str, Any], op: MapOp) -> Dict[str, Any]:
        transformer = OP_TRANSFORMERS.get(op.get("op", ""), lambda res, _: res)
        return transformer(current, op)

    from functools import reduce
    return reduce(_apply_op, ops, dict(data))
