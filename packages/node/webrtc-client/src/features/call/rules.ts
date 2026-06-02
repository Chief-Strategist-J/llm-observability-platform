import type { CallStatus, MessageType } from "./types";

export function isRelayMessage(type: MessageType): boolean {
  return type === "offer" || type === "answer" || type === "ice-candidate";
}

export function isPeerEvent(type: MessageType): boolean {
  return type === "peer-joined" || type === "peer-left";
}

export function shouldRestartIce(status: CallStatus): boolean {
  return status === "connected" || status === "negotiating";
}

export function isTerminalStatus(status: CallStatus): boolean {
  return status === "disconnected" || status === "error";
}
