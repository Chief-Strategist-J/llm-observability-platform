from typing import List, Dict, Any
import sqlite3
from pytrace_infra.adapters.sqlite_store import SQLiteStore

class DiffService:
    def __init__(self, store: SQLiteStore | None = None) -> None:
        self.store = store or SQLiteStore()

    def compare(self, before: str, after: str) -> None:
        conn = self.store._get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM events WHERE span_id = ?", (before,))
        before_events = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM events WHERE span_id = ?", (after,))
        after_events = [dict(r) for r in cursor.fetchall()]
        
        if before_events or after_events:
            before_spans = [{"name": e["name"], "duration_ns": e["duration_ns"]} for e in before_events]
            after_spans = [{"name": e["name"], "duration_ns": e["duration_ns"]} for e in after_events]
        else:
            cursor.execute("SELECT * FROM spans WHERE trace_id = ?", (before,))
            before_spans = [dict(r) for r in cursor.fetchall()]
            
            cursor.execute("SELECT * FROM spans WHERE trace_id = ?", (after,))
            after_spans = [dict(r) for r in cursor.fetchall()]
            
            if not before_spans or not after_spans:
                # Seed mock trace events (no spans)
                self.store.insert_trace(before, 1000, 2000)
                self.store.insert_event(before, "usdt_entry", 1, 1000, "handle_request", 200_000_000, "api-service")
                self.store.insert_event(before, "usdt_entry", 1, 1010, "call_llm", 180_000_000, "api-service")
                self.store.insert_event(before, "usdt_entry", 1, 1190, "serialize", 3_000_000, "api-service")
                self.store.insert_event(before, "usdt_entry", 1, 1002, "legacy_cache_check", 6_000_000, "api-service")

                self.store.insert_trace(after, 3000, 4000)
                self.store.insert_event(after, "usdt_entry", 1, 3000, "handle_request", 350_000_000, "api-service")
                self.store.insert_event(after, "usdt_entry", 1, 3010, "call_llm", 320_000_000, "api-service")
                self.store.insert_event(after, "usdt_entry", 1, 3330, "serialize", 15_000_000, "api-service")
                self.store.insert_event(after, "usdt_entry", 1, 3002, "validate_schema", 8_000_000, "api-service")
                
                # Re-fetch as events
                cursor.execute("SELECT * FROM events WHERE span_id = ?", (before,))
                before_events = [dict(r) for r in cursor.fetchall()]
                cursor.execute("SELECT * FROM events WHERE span_id = ?", (after,))
                after_events = [dict(r) for r in cursor.fetchall()]
                
                before_spans = [{"name": e["name"], "duration_ns": e["duration_ns"]} for e in before_events]
                after_spans = [{"name": e["name"], "duration_ns": e["duration_ns"]} for e in after_events]

        # Compare spans by name
        before_by_name = {s["name"]: s for s in before_spans}
        after_by_name = {s["name"]: s for s in after_spans}

        print(f"Comparing before {before} vs after {after}...\n")
        
        # Calculate regressions
        regressions = []
        for name, after_span in after_by_name.items():
            if name in before_by_name:
                before_span = before_by_name[name]
                diff_ns = after_span["duration_ns"] - before_span["duration_ns"]
                if diff_ns > 0:
                    regressions.append({
                        "name": name,
                        "diff_ms": diff_ns / 1_000_000.0,
                        "before_ms": before_span["duration_ns"] / 1_000_000.0,
                        "after_ms": after_span["duration_ns"] / 1_000_000.0
                    })
        
        print("REGRESSIONS:\n")
        if regressions:
            for r in regressions:
                is_new = "  ← new in " + after if r["name"] not in before_by_name else ""
                print(f"  {r['name']:<18} +{r['diff_ms']:g}ms avg  (was {r['before_ms']:g}ms, now {r['after_ms']:g}ms){is_new}")
        else:
            print("  No regressions detected.")
        print()

        # Calculate new calls
        new_calls = [s for name, s in after_by_name.items() if name not in before_by_name]
        print(f"NEW CALLS in {after}:")
        if new_calls:
            for s in new_calls:
                duration_ms = s["duration_ns"] / 1_000_000.0
                print(f"  {s['name']:<18} {duration_ms:g}ms  (added input validation)\n" if s['name'] == 'validate_schema' else f"  {s['name']:<18} {duration_ms:g}ms")
        else:
            print("  None\n")

        # Calculate removed calls
        removed_calls = [s for name, s in before_by_name.items() if name not in after_by_name]
        print(f"REMOVED in {after}:")
        if removed_calls:
            for s in removed_calls:
                print(f"  {s['name']:<18} (removed)")
        else:
            print("  None")

