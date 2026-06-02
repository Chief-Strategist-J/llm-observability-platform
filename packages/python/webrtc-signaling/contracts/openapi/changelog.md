# Signaling API Changelog

## [1.0.0] — 2026-06-02

### Added
- `GET /health` — liveness probe
- `GET /ws/{room_id}` — WebSocket upgrade for named-room signaling
- `SignalMessage` schema covering `offer`, `answer`, `ice-candidate`, `peer-joined`, `peer-left`, `error`
- `ErrorMessage` schema
