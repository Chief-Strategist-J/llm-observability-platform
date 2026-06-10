from typing import Protocol, List, Dict, Any

class TraceCollectorPort(Protocol):
    def attach(self, pid: int) -> bool:
        """Attach to python process and collect OTel + bpftrace events."""
        ...

    def stop_collection(self) -> None:
        """Stop tracing collection."""
        ...

    def get_events(self) -> List[Dict[str, Any]]:
        """Retrieve unified events collected."""
        ...
