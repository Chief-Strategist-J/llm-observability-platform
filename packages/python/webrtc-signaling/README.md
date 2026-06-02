# WebRTC Signaling Server

A clean, high-performance WebSocket signaling server for 1-on-1 audio/video calling, implemented in Python using FastAPI.

---

## Architectural Layout (Hexagonal Architecture)

```
packages/python/webrtc-signaling/
├── src/
│   ├── api/
│   │   └── rest/v1/                   # REST Healthchecks and WebSocket connection endpoint
│   ├── features/
│   │   └── signal_session/            # Core Session Management Feature
│   │       ├── index.py               # Feature entry point
│   │       ├── service.py             # Signaling logic
│   │       └── types.py               # Feature-specific types
│   ├── shared/
│   │   └── ports/                     # Ports (Contracts) definition
│   │       ├── session_store.py       # SessionStorePort contract
│   │       └── signaling_port.py      # ISignalingPort contract
│   └── infra/
│       └── adapters/                  # Adapters (Implementations)
│           └── in_memory/             # InMemorySessionStore Adapter
└── tests/
    └── unit/                          # Isolated unit tests
```

---

## Decision Logic Tree

```
Incoming Connection
└── WS Connection Established
    ├── Handshake & Client Registration
    └── Wait for Signaling Commands
        ├── join-room
        │   ├── Store Peer Session ID
        │   └── If room has another peer:
        │       └── Send "peer-joined" to both
        ├── offer / answer
        │   ├── Forward Session Description to other peer
        │   └── If other peer not found: raise error
        ├── ice-candidate
        │   ├── Forward ICE Candidate payload to other peer
        │   └── If other peer not found: raise error
        └── disconnect
            ├── Remove Peer Session ID
            └── Notify room partner of exit
```

---

## How to Use this Package

### Prerequisites
- Python 3.12+
- `pip`

### 1. Installation
Install the package and dependencies in development mode:
```bash
pip install -e .
```

### 2. Run the server
You can start the server locally using the run script:
```bash
./scripts/run.sh
```
Or run `uvicorn` directly:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8010 --reload
```

### 3. Running tests
```bash
pytest tests/unit/
```

### 4. Build Docker image
```bash
docker build -t chiefj/webrtc-signaling:latest -f build/Dockerfile .
```
