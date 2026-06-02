import threading
from collections import defaultdict

from opentelemetry import trace

_tracer = trace.get_tracer("webrtc-signaling.session_store")


class MemorySessionStoreAdapter:
    def __init__(self) -> None:
        self._rooms: dict[str, list[str]] = defaultdict(list)
        self._lock = threading.Lock()

    def add_peer(self, room_id: str, peer_id: str) -> None:
        with _tracer.start_as_current_span("memory_store.add_peer") as span:
            span.set_attribute("room_id", room_id)
            span.set_attribute("peer_id", peer_id)
            with self._lock:
                if peer_id not in self._rooms[room_id]:
                    self._rooms[room_id].append(peer_id)

    def remove_peer(self, room_id: str, peer_id: str) -> None:
        with _tracer.start_as_current_span("memory_store.remove_peer") as span:
            span.set_attribute("room_id", room_id)
            span.set_attribute("peer_id", peer_id)
            with self._lock:
                if peer_id in self._rooms.get(room_id, []):
                    self._rooms[room_id].remove(peer_id)
                if not self._rooms.get(room_id):
                    self._rooms.pop(room_id, None)

    def get_peers(self, room_id: str) -> list[str]:
        with _tracer.start_as_current_span("memory_store.get_peers") as span:
            span.set_attribute("room_id", room_id)
            with self._lock:
                result = list(self._rooms.get(room_id, []))
            span.set_attribute("peer_count", len(result))
            return result

    def room_exists(self, room_id: str) -> bool:
        with self._lock:
            return room_id in self._rooms
