from dataclasses import dataclass
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    OFFER = "offer"
    ANSWER = "answer"
    ICE_CANDIDATE = "ice-candidate"
    PEER_JOINED = "peer-joined"
    PEER_LEFT = "peer-left"
    ERROR = "error"


class PeerRole(str, Enum):
    OFFERER = "offerer"
    ANSWERER = "answerer"


@dataclass(frozen=True)
class SignalMessage:
    type: MessageType
    room_id: str
    payload: dict[str, Any] | None = None


@dataclass(frozen=True)
class PeerSession:
    peer_id: str
    room_id: str
    role: PeerRole
