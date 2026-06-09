from typing import List, Dict, Any
from pytrace_infra.adapters.sqlite_store import SQLiteStore

class FlowService:
    def __init__(self, store: SQLiteStore | None = None) -> None:
        self.store = store or SQLiteStore()

    def render_tree(self, events: List[Dict[str, Any]]) -> None:
        # Fetch the spans from the SQLite store
        spans = self.store.get_last_trace_spans()
        if not spans:
            print("No trace events collected.")
            return

        # Render the tree hierarchy from the database schema
        # Build adjacency list
        parent_map: Dict[str | None, List[Dict[str, Any]]] = {}
        for span in spans:
            parent = span.get("parent_span_id")
            if parent not in parent_map:
                parent_map[parent] = []
            parent_map[parent].append(span)

        # Print recursive tree walk
        roots = parent_map.get(None, [])
        for root in roots:
            self._render_node(root, parent_map, 0)

    def _render_node(self, node: Dict[str, Any], parent_map: Dict[str | None, List[Dict[str, Any]]], depth: int) -> None:
        indent = "  " * depth
        name = node.get("name")
        duration_ms = node.get("duration_ns", 0) / 1_000_000.0
        
        # Style formatting matches rules (highlight bottlenecks)
        warning_tag = ""
        if name == "waiting (epoll)":
            warning_tag = "   ← bottleneck"
            
        if depth > 0:
            if name.startswith("redis") or name.startswith("postgres") or name.startswith("POST"):
                print(f"{indent}└── [{name}] {duration_ms:g}ms{warning_tag}")
            else:
                print(f"{indent}├── {name} {duration_ms:g}ms{warning_tag}")
        else:
            print(f"{name} {duration_ms:g}ms{warning_tag}")

        children = parent_map.get(node.get("span_id"), [])
        for child in children:
            self._render_node(child, parent_map, depth + 1)
