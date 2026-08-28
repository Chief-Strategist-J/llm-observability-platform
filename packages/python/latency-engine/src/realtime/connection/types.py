from enum import Enum

class ConnectionState(str, Enum):
    CONNECTED = "connected"
    CONNECTING = "connecting"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"
