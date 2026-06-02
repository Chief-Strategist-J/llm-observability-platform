import "./style.css";
import { initTracer } from "./shared/tracing/tracer";
import { buildCallService } from "./shared/di/container";
import type { CallState } from "./features/call/types";
import { BrowserMediaAdapter } from "./infra/adapters/webrtc/rtc_peer_adapter";

initTracer();

const media = new BrowserMediaAdapter();
let callService: ReturnType<typeof buildCallService> | null = null;

const joinPanel = document.getElementById("join-panel") as HTMLElement;
const callPanel = document.getElementById("call-panel") as HTMLElement;
const roomInput = document.getElementById("room-input") as HTMLInputElement;
const joinBtn = document.getElementById("join-btn") as HTMLButtonElement;
const muteBtn = document.getElementById("mute-btn") as HTMLButtonElement;
const camBtn = document.getElementById("cam-btn") as HTMLButtonElement;
const hangBtn = document.getElementById("hang-btn") as HTMLButtonElement;
const remoteVideo = document.getElementById("remote-video") as HTMLVideoElement;
const localVideo = document.getElementById("local-video") as HTMLVideoElement;
const statusBadge = document.getElementById("status-badge") as HTMLElement;

function applyState(state: CallState): void {
  const statusMap: Record<CallState["status"], [string, string]> = {
    idle: ["Idle", "badge--idle"],
    connecting: ["Connecting…", "badge--waiting"],
    "waiting-for-peer": ["Waiting for peer…", "badge--waiting"],
    negotiating: ["Negotiating…", "badge--negotiating"],
    connected: ["Connected", "badge--connected"],
    disconnected: ["Disconnected", "badge--idle"],
    error: ["Error", "badge--error"],
  };

  const [label, cls] = statusMap[state.status];
  statusBadge.textContent = label;
  statusBadge.className = `badge ${cls}`;

  if (state.localStream) {
    media.attachLocalStream(state.localStream, localVideo);
  }
  if (state.remoteStream) {
    media.attachRemoteStream(state.remoteStream, remoteVideo);
  }

  if (state.status === "disconnected" || state.status === "error") {
    joinPanel.classList.remove("hidden");
    callPanel.classList.add("hidden");
  }
}

joinBtn.addEventListener("click", async () => {
  const roomId = roomInput.value.trim();
  if (!roomId || roomId.length < 3) {
    roomInput.focus();
    return;
  }

  joinPanel.classList.add("hidden");
  callPanel.classList.remove("hidden");

  const signalingBaseUrl =
    (import.meta.env["VITE_SIGNALING_URL"] as string | undefined) ?? `ws://${location.hostname}:8010`;

  callService = buildCallService({ roomId, signalingBaseUrl, onStateChange: applyState });
  await callService.start();
});

roomInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") joinBtn.click();
});

muteBtn.addEventListener("click", () => {
  const track = (localVideo.srcObject as MediaStream | null)?.getAudioTracks()[0];
  if (track) {
    track.enabled = !track.enabled;
    muteBtn.classList.toggle("ctrl-btn--muted", !track.enabled);
  }
});

camBtn.addEventListener("click", () => {
  const track = (localVideo.srcObject as MediaStream | null)?.getVideoTracks()[0];
  if (track) {
    track.enabled = !track.enabled;
    camBtn.classList.toggle("ctrl-btn--muted", !track.enabled);
  }
});

hangBtn.addEventListener("click", () => {
  callService?.stop();
  callService = null;
  joinPanel.classList.remove("hidden");
  callPanel.classList.add("hidden");
  statusBadge.textContent = "Idle";
  statusBadge.className = "badge badge--idle";
  remoteVideo.srcObject = null;
  localVideo.srcObject = null;
});
