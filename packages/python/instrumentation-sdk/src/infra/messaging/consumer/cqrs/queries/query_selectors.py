from typing import Dict, Any
from .projection_store import projection_store

class QuerySelectors:
    @staticmethod
    def get_session_summary(session_id: str) -> Dict[str, Any]:
        return projection_store.get_projection(session_id)

query_selectors = QuerySelectors()
