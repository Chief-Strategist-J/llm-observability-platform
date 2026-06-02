from src.features.signal_session.rules import (
    is_relay_message,
    is_room_full,
    is_valid_room_id,
    validate_signal_message,
)
from src.features.signal_session.types import MessageType


class TestIsValidRoomId:
    def test_accepts_alphanumeric(self):
        assert is_valid_room_id("room123") is True

    def test_accepts_hyphens_and_underscores(self):
        assert is_valid_room_id("my-room_01") is True

    def test_rejects_too_short(self):
        assert is_valid_room_id("ab") is False

    def test_rejects_too_long(self):
        assert is_valid_room_id("a" * 65) is False

    def test_rejects_special_chars(self):
        assert is_valid_room_id("room!id") is False


class TestIsRoomFull:
    def test_not_full_with_zero_peers(self):
        assert is_room_full(0) is False

    def test_not_full_with_one_peer(self):
        assert is_room_full(1) is False

    def test_full_with_two_peers(self):
        assert is_room_full(2) is True

    def test_full_exceeding_limit(self):
        assert is_room_full(3) is True


class TestIsRelayMessage:
    def test_offer_is_relay(self):
        assert is_relay_message(MessageType.OFFER) is True

    def test_answer_is_relay(self):
        assert is_relay_message(MessageType.ANSWER) is True

    def test_ice_candidate_is_relay(self):
        assert is_relay_message(MessageType.ICE_CANDIDATE) is True

    def test_peer_joined_is_not_relay(self):
        assert is_relay_message(MessageType.PEER_JOINED) is False

    def test_error_is_not_relay(self):
        assert is_relay_message(MessageType.ERROR) is False


class TestValidateSignalMessage:
    def test_valid_offer_message(self):
        raw = {"type": "offer", "room_id": "abc123", "payload": {"sdp": "..."}}
        result = validate_signal_message(raw)
        assert result is not None
        assert result.type == MessageType.OFFER

    def test_invalid_message_type_returns_none(self):
        raw = {"type": "unknown", "room_id": "abc123"}
        assert validate_signal_message(raw) is None

    def test_invalid_room_id_returns_none(self):
        raw = {"type": "offer", "room_id": "!!"}
        assert validate_signal_message(raw) is None

    def test_message_without_payload_is_valid(self):
        raw = {"type": "ice-candidate", "room_id": "abc123"}
        result = validate_signal_message(raw)
        assert result is not None
        assert result.payload is None
