# 1-on-1 WebRTC Calling Platform Deployment Guide

A fully open-source, lightweight, high-performance 1-on-1 audio/video calling platform powered by WebRTC. 
* **Backend**: Python (FastAPI + WebSockets)
* **Frontend**: TypeScript (Vite + plain DOM)
* **Network Traversal**: Self-hosted `coturn` STUN/TURN server

---

## Architecture Overview

This platform is built using **Hexagonal Architecture (Ports and Adapters)**:
- The domain layer is pure, with zero runtime/infrastructure dependencies.
- It interfaces with the outside world via ports (`SessionStorePort`, `ISignalingPort`, `IMediaPort`).
- Infrastructure details (WebSockets, Browser RTCPeerConnection APIs, Coturn TURN server) are adapters that plug into these ports.

---

## Quick Start (Run with Docker Compose)

To spin up the entire platform (signaling server, coturn server, and client frontend) with a single command, use the unified `docker-compose.yaml`.

### 1. Prerequisites
Ensure you have Docker and Docker Compose installed on your host machine.

### 2. Startup
Navigate to the directory containing this guide and run:
```bash
docker compose up -d
```

This pulls and starts the following services:
- **Client Frontend**: `chiefj/webrtc-client:latest` (Nginx serving static assets on port `3000`)
- **Signaling Backend**: `chiefj/webrtc-signaling:latest` (FastAPI WebSocket server on port `8010`)
- **Coturn TURN**: `coturn/coturn:latest` (STUN/TURN server on host port `3478`)

### 3. Verify Status
Ensure all containers are healthy:
```bash
docker compose ps
```

---

## How to Connect & Work with the Platform

### 1. Join a Call
1. Open your browser and navigate to `http://localhost:3000`.
2. Enter a room name (minimum 3 characters, e.g., `lobby-42`) in the join panel.
3. Click **Join**. You will see your own local camera feed.
4. Open another browser tab or a browser on another machine pointing to the same address.
5. Enter the **exact same room name** and click **Join**.
6. The signaling server will pair both peers, exchange WebRTC offers/answers/ICE candidates, and connect the call directly.

### 2. In-Call Controls
Once connected, the screen displays the remote stream in full screen and your local preview in the corner. You can control your call with the bottom bar:
- 🎙️ **Toggle Microphone**: Mutes or unmutes your audio track.
- 📷 **Toggle Camera**: Enables or disables your video feed.
- 📵 **Hang Up**: Closes connections and returns to the join screen.

---

## Public Production Deployment

When deploying outside `localhost` (e.g., to an AWS, GCP, or DigitalOcean VM), WebRTC requires a secure context (HTTPS) and appropriate STUN/TURN addressing.

### 1. Signaling URL
Update `VITE_SIGNALING_URL` in the client container environment to your public signaling domain:
```yaml
environment:
  - VITE_SIGNALING_URL=wss://signaling.yourdomain.com
```

### 2. TURN Server Public IP Configuration
For coturn to relay traffic between peers behind symmetric NATs over the internet, update `./coturn.conf` with your server's external IP:
```ini
# Add to coturn.conf
external-ip=<YOUR_SERVER_PUBLIC_IP>
```
Make sure port `3478` (UDP & TCP) and the UDP relay ports (`49152-65535`) are open on your host's firewall.
