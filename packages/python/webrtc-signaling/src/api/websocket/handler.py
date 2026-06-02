import json
import uuid
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from opentelemetry import trace

from src.features.signal_session.rules import validate_signal_message
from src.features.signal_session.service import SessionManagerService
from src.features.signal_session.types import MessageType, SignalMessage

_tracer = trace.get_tracer("webrtc-signaling.ws_handler")

_active_connections: dict[str, WebSocket] = {}


async def _send(ws: WebSocket, message: SignalMessage) -> None:
    payload: dict[str, Any] = {"type": message.type.value, "room_id": message.room_id}
    if message.payload is not None:
        payload["payload"] = message.payload
    await ws.send_text(json.dumps(payload))


async def handle_websocket(
    websocket: WebSocket,
    room_id: str,
    manager: SessionManagerService,
) -> None:
    peer_id = str(uuid.uuid4())

    with _tracer.start_as_current_span("ws_handler.connect") as span:
        span.set_attribute("room_id", room_id)
        span.set_attribute("peer_id", peer_id)

        session = manager.join_room(room_id, peer_id)
        if session is None:
            await websocket.close(code=4009, reason="Room full or invalid room_id")
            span.set_attribute("rejected", True)
            return

        await websocket.accept()
        _active_connections[peer_id] = websocket
        span.set_attribute("role", session.role.value)

        relay_target = manager.get_relay_target(room_id, peer_id)
        if relay_target and relay_target in _active_connections:
            joined_msg = manager.build_peer_joined_message(room_id)
            await _send(_active_connections[relay_target], joined_msg)

    try:
        while True:
            raw_text = await websocket.receive_text()
            with _tracer.start_as_current_span("ws_handler.message") as msg_span:
                msg_span.set_attribute("peer_id", peer_id)
                raw = json.loads(raw_text)
                message = validate_signal_message(raw)

                if message is None:
                    error_msg = SignalMessage(
                        type=MessageType.ERROR,
                        room_id=room_id,
                        payload={"code": "SIG-003", "detail": "Invalid message"},
                    )
                    await _send(websocket, error_msg)
                    continue

                if manager.is_relay_message(message):
                    target_id = manager.get_relay_target(room_id, peer_id)
                    if target_id and target_id in _active_connections:
                        await _send(_active_connections[target_id], message)
                        msg_span.set_attribute("relayed_to", target_id)

    except WebSocketDisconnect:
        pass
    finally:
        with _tracer.start_as_current_span("ws_handler.disconnect") as span:
            span.set_attribute("peer_id", peer_id)
            span.set_attribute("room_id", room_id)
            _active_connections.pop(peer_id, None)
            manager.leave_room(room_id, peer_id)

            relay_target = manager.get_relay_target(room_id, peer_id)
            if relay_target and relay_target in _active_connections:
                left_msg = manager.build_peer_left_message(room_id)
                await _send(_active_connections[relay_target], left_msg)
