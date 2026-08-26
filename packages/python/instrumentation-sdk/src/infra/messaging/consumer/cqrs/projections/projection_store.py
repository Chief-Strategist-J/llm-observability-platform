from typing import Dict, Any, List

class MaterializedProjectionStore:
    def __init__(self) -> None:
        self._projections: Dict[str, Dict[str, Any]] = {}

    def apply_event(self, event_type: str, aggregate_id: str, payload: Dict[str, Any]) -> None:
        current = self._projections.get(aggregate_id, {"aggregate_id": aggregate_id, "event_count": 0, "total_cost_usd_micro": 0})
        current["event_count"] += 1
        current["total_cost_usd_micro"] += payload.get("cost_usd_micro", 0)
        current["last_event"] = event_type
        self._projections[aggregate_id] = current

    def get_projection(self, aggregate_id: str) -> Dict[str, Any]:
        return self._projections.get(aggregate_id, {})

projection_store = MaterializedProjectionStore()
