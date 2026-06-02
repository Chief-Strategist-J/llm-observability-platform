import pytest

from src.features.signal_session.service import SessionManagerService
from src.features.signal_session.types import MessageType, PeerRole, SignalMessage


class FakeSessionStore:
    def __init__(self):
        self._rooms: dict[str, list[str]] = {}

    def add_peer(self, room_id: str, peer_id: str) -> None:
        self._rooms.setdefault(room_id, [])
        if peer_id not in self._rooms[room_id]:
            self._rooms[room_id].append(peer_id)

    def remove_peer(self, room_id: str, peer_id: str) -> None:
        if peer_id in self._rooms.get(room_id, []):
            self._rooms[room_id].remove(peer_id)

    def get_peers(self, room_id: str) -> list[str]:
        return list(self._rooms.get(room_id, []))

    def room_exists(self, room_id: str) -> bool:
        return room_id in self._rooms


@pytest.fixture
def manager():
    return SessionManagerService(store=FakeSessionStore())


class TestJoinRoom:
    def test_first_peer_gets_offerer_role(self, manager):
        session = manager.join_room("room-a", "peer-1")
        assert session is not None
        assert session.role == PeerRole.OFFERER

    def test_second_peer_gets_answerer_role(self, manager):
        manager.join_room("room-a", "peer-1")
        session = manager.join_room("room-a", "peer-2")
        assert session is not None
        assert session.role == PeerRole.ANSWERER

    def test_third_peer_is_rejected(self, manager):
        manager.join_room("room-a", "peer-1")
        manager.join_room("room-a", "peer-2")
        session = manager.join_room("room-a", "peer-3")
        assert session is None

    def test_invalid_room_id_is_rejected(self, manager):
        session = manager.join_room("!!", "peer-1")
        assert session is None


class TestLeaveRoom:
    def test_peer_is_removed_after_leave(self, manager):
        manager.join_room("room-b", "peer-1")
        manager.leave_room("room-b", "peer-1")
        session = manager.join_room("room-b", "peer-new")
        assert session is not None
        assert session.role == PeerRole.OFFERER


class TestGetRelayTarget:
    def test_returns_other_peer(self, manager):
        manager.join_room("room-c", "peer-1")
        manager.join_room("room-c", "peer-2")
        target = manager.get_relay_target("room-c", "peer-1")
        assert target == "peer-2"

    def test_returns_none_when_alone(self, manager):
        manager.join_room("room-d", "peer-1")
        target = manager.get_relay_target("room-d", "peer-1")
        assert target is None


class TestRelayMessageCheck:
    def test_offer_is_relay(self, manager):
        msg = SignalMessage(type=MessageType.OFFER, room_id="r")
        assert manager.is_relay_message(msg) is True

    def test_peer_joined_is_not_relay(self, manager):
        msg = SignalMessage(type=MessageType.PEER_JOINED, room_id="r")
        assert manager.is_relay_message(msg) is False
