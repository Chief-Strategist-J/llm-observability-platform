from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from src.api.websocket.handler import handle_websocket
from src.shared.di.providers import build_session_manager
from src.shared.tracing.tracer import init_tracer

init_tracer()

_manager = build_session_manager()

app = FastAPI(
    title="WebRTC Signaling Server",
    version="1.0.0",
    description="Relay-only signaling server for 1-on-1 WebRTC audio/video calls",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str) -> None:
    await handle_websocket(websocket, room_id, _manager)
