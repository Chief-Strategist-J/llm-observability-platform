from opentelemetry import trace

from src.features.signal_session.rules import is_relay_message, is_room_full, is_valid_room_id
from src.features.signal_session.types import MessageType, PeerRole, PeerSession, SignalMessage
from src.shared.ports.session_store_port import SessionStorePort

_tracer = trace.get_tracer("webrtc-signaling.session_manager")


class SessionManagerService:
    def __init__(self, store: SessionStorePort) -> None:
        self._store = store

    def join_room(self, room_id: str, peer_id: str) -> PeerSession | None:
        with _tracer.start_as_current_span("session_manager.join_room") as span:
            span.set_attribute("room_id", room_id)
            span.set_attribute("peer_id", peer_id)

            if not is_valid_room_id(room_id):
                span.set_attribute("error", "invalid_room_id")
                return None

            peers = self._store.get_peers(room_id)
            if is_room_full(len(peers)):
                span.set_attribute("error", "room_full")
                return None

            role = PeerRole.OFFERER if len(peers) == 0 else PeerRole.ANSWERER
            self._store.add_peer(room_id, peer_id)
            span.set_attribute("role", role.value)
            return PeerSession(peer_id=peer_id, room_id=room_id, role=role)

    def leave_room(self, room_id: str, peer_id: str) -> None:
        with _tracer.start_as_current_span("session_manager.leave_room") as span:
            span.set_attribute("room_id", room_id)
            span.set_attribute("peer_id", peer_id)
            self._store.remove_peer(room_id, peer_id)

    def get_relay_target(self, room_id: str, sender_peer_id: str) -> str | None:
        with _tracer.start_as_current_span("session_manager.get_relay_target") as span:
            span.set_attribute("room_id", room_id)
            peers = self._store.get_peers(room_id)
            targets = [p for p in peers if p != sender_peer_id]
            result = targets[0] if targets else None
            span.set_attribute("target_found", result is not None)
            return result

    def is_relay_message(self, message: SignalMessage) -> bool:
        return is_relay_message(message.type)

    def build_peer_joined_message(self, room_id: str) -> SignalMessage:
        return SignalMessage(type=MessageType.PEER_JOINED, room_id=room_id)

    def build_peer_left_message(self, room_id: str) -> SignalMessage:
        return SignalMessage(type=MessageType.PEER_LEFT, room_id=room_id)
