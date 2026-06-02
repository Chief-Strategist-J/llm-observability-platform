import re

from src.features.signal_session.types import MessageType, SignalMessage

_ROOM_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")
_MAX_PEERS_PER_ROOM = 2


def is_valid_room_id(room_id: str) -> bool:
    return bool(_ROOM_ID_PATTERN.match(room_id))


def is_room_full(peer_count: int) -> bool:
    return peer_count >= _MAX_PEERS_PER_ROOM


def is_relay_message(message_type: MessageType) -> bool:
    return message_type in {MessageType.OFFER, MessageType.ANSWER, MessageType.ICE_CANDIDATE}


def validate_signal_message(raw: dict) -> SignalMessage | None:
    try:
        msg_type = MessageType(raw.get("type", ""))
    except ValueError:
        return None
    room_id = raw.get("room_id", "")
    if not is_valid_room_id(room_id):
        return None
    return SignalMessage(type=msg_type, room_id=room_id, payload=raw.get("payload"))
