# WebRTC UI Client

A responsive, high-fidelity browser client for 1-on-1 audio/video calling, implemented in TypeScript using Vite and plain DOM interfaces.

---

## Architectural Layout (Hexagonal Architecture)

```
packages/node/webrtc-client/
├── src/
│   ├── shared/
│   │   └── ports/                     # Infrastructure Ports
│   │       ├── media_port.ts          # IMediaPort interface
│   │       └── signaling_port.ts      # ISignalingPort interface
│   ├── infra/
│   │   └── adapters/                  # Infrastructure Adapters
│   │       ├── webrtc_media.ts        # Browser RTCPeerConnection API Adapter
│   │       └── ws_signaling.ts        # Browser WebSocket API Adapter
│   ├── features/
│   │   └── call/                      # Call Logic Feature
│   │       ├── service.ts             # WebRTC caller state machine and handler logic
│   │       ├── ui.ts                  # DOM View controller and user interactions
│   │       └── rules.ts               # Local validation rules
│   └── main.ts                        # Application bootstrap
└── tests/
    └── unit/                          # Isolated unit tests
```

---

## Call Logic Decision Tree

```
User Action: Click "Join"
├── Validate input room name
└── Connect via ISignalingPort WebSocket
    ├── Join request sent to signaling server
    └── Wait for room partner
        ├── Partner Joins -> Initiator Peer creates Offer
        │   ├── Set local description (SDP)
        │   └── Send "offer" message to Partner
        ├── Received "offer" -> Receiver Peer creates Answer
        │   ├── Set remote description (SDP)
        │   ├── Set local description (SDP)
        │   └── Send "answer" message to Partner
        ├── Received "answer"
        │   └── Set remote description (SDP)
        └── ICE Candidate Exchange
            ├── Local ICE candidate found -> Send "ice-candidate"
            └── Received "ice-candidate" -> Add to Peer Connection
```

---

## How to Use this Package

### Prerequisites
- Node.js 20+
- npm

### 1. Installation
Install project dependencies:
```bash
npm install --legacy-peer-deps
```

### 2. Development Startup
Start the local development server:
```bash
npm run dev
```
Open `http://localhost:3000` in your web browser.

### 3. Running Unit Tests
```bash
npm run test
```

### 4. Build and Production Preview
```bash
npm run build
npm run preview
```

### 5. Build Docker Image
```bash
docker build -t chiefj/webrtc-client:latest -f build/Dockerfile .
```
