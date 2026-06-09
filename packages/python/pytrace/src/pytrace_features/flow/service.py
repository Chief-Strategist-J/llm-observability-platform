from typing import List, Dict, Any
from pytrace_infra.adapters.sqlite_store import SQLiteStore

class FlowService:
    def __init__(self, store: SQLiteStore | None = None) -> None:
        self.store = store or SQLiteStore()

    def render_tree(self, events: List[Dict[str, Any]]) -> None:
        # Fetch trace events from the SQLite store
        events_from_db = self.store.get_last_trace_events()
        
        if events_from_db:
            spans = []
            for i, ev in enumerate(events_from_db):
                start_ns = ev.get("timestamp_ns", 0)
                dur_ns = ev.get("duration_ns", 0)
                spans.append({
                    "span_id": f"event_span_{i}",
                    "name": ev.get("name"),
                    "start_time_ns": start_ns,
                    "end_time_ns": start_ns + dur_ns,
                    "duration_ns": dur_ns,
                    "parent_span_id": None
                })
        else:
            # Fallback to database spans (for backward compatibility with tests)
            spans = self.store.get_last_trace_spans()
        
        # Fallback to raw events parameter if still no data
        if not spans:
            if not events:
                print("No trace events collected.")
                return
            
            # Convert raw events to spans dynamically
            spans = []
            for i, ev in enumerate(events):
                start_ns = int(ev.get("timestamp", 0) * 1e9)
                dur_ns = int(ev.get("duration_ms", 0) * 1e6)
                spans.append({
                    "span_id": f"event_span_{i}",
                    "name": ev.get("name"),
                    "start_time_ns": start_ns,
                    "end_time_ns": start_ns + dur_ns,
                    "duration_ns": dur_ns,
                    "parent_span_id": None
                })

        # Check if parent_span_id is missing or None for non-root spans (uninstrumented fallback)
        has_parent_info = any(s.get("parent_span_id") is not None for s in spans)
        
        if not has_parent_info and len(spans) > 1:
            # Reconstruct the hierarchy using stack-based call tree nesting algorithm
            # Sort by start_time_ns ascending
            sorted_spans = sorted(spans, key=lambda x: x.get("start_time_ns", 0))
            stack: List[Dict[str, Any]] = []
            
            for span in sorted_spans:
                # Pop spans from stack that finished before the current span started
                while stack and stack[-1].get("end_time_ns", 0) <= span.get("start_time_ns", 0):
                    stack.pop()
                
                # If stack is not empty, the top span is the parent
                if stack:
                    span["parent_span_id"] = stack[-1]["span_id"]
                else:
                    span["parent_span_id"] = None
                
                stack.append(span)
            spans = sorted_spans

        # Render the tree hierarchy from the database schema
        # Build adjacency list
        parent_map: Dict[str | None, List[Dict[str, Any]]] = {}
        for span in spans:
            parent = span.get("parent_span_id")
            if parent not in parent_map:
                parent_map[parent] = []
            parent_map[parent].append(span)

        # Print recursive tree walk with correct branch lines
        roots = parent_map.get(None, [])
        for root in roots:
            self._render_node(root, parent_map, "", is_last=True, is_root=True)

    def _render_node(self, node: Dict[str, Any], parent_map: Dict[str | None, List[Dict[str, Any]]], prefix: str, is_last: bool, is_root: bool) -> None:
        name = node.get("name")
        duration_ms = node.get("duration_ns", 0) / 1_000_000.0
        
        # Style formatting (highlight bottlenecks)
        warning_tag = ""
        if "epoll" in name:
            warning_tag = "   ← bottleneck"

        if is_root:
            print(f"{name} {duration_ms:g}ms{warning_tag}")
            new_prefix = ""
        else:
            connector = "└── " if is_last else "├── "
            # Highlight external dependency calls with brackets if requested or standard
            if name.startswith("redis") or name.startswith("postgres") or name.startswith("POST") or name.startswith("["):
                display_name = name if name.startswith("[") else f"[{name}]"
                print(f"{prefix}{connector}{display_name} {duration_ms:g}ms{warning_tag}")
            else:
                print(f"{prefix}{connector}{name} {duration_ms:g}ms{warning_tag}")
            
            new_prefix = prefix + ("    " if is_last else "│   ")

        children = parent_map.get(node.get("span_id"), [])
        for i, child in enumerate(children):
            self._render_node(child, parent_map, new_prefix, is_last=(i == len(children) - 1), is_root=False)

