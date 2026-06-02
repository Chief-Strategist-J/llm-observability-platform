import { BrowserMediaAdapter } from "@infra/adapters/webrtc/rtc_peer_adapter";
import { SignalingRepository } from "@features/call/repository";
import { CallService } from "@features/call/service";
import type { CallState } from "@features/call/types";

export interface CallServiceConfig {
  roomId: string;
  signalingBaseUrl: string;
  onStateChange: (state: CallState) => void;
}

export function buildCallService(config: CallServiceConfig): CallService {
  const signaling = new SignalingRepository(config.signalingBaseUrl);
  const media = new BrowserMediaAdapter();
  const iceServers: RTCIceServer[] = [
    { urls: "stun:stun.l.google.com:19302" },
    { urls: "stun:stun1.l.google.com:19302" },
    {
      urls: "turn:localhost:3478",
      username: import.meta.env["VITE_TURN_USER"] ?? "webrtc",
      credential: import.meta.env["VITE_TURN_CREDENTIAL"] ?? "webrtc123",
    },
  ];
  return new CallService(signaling, media, config.roomId, iceServers, config.onStateChange);
}
