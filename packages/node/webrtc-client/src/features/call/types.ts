export type MessageType =
  | "offer"
  | "answer"
  | "ice-candidate"
  | "peer-joined"
  | "peer-left"
  | "error";

export type PeerRole = "offerer" | "answerer";

export type CallStatus =
  | "idle"
  | "connecting"
  | "waiting-for-peer"
  | "negotiating"
  | "connected"
  | "disconnected"
  | "error";

export interface SignalMessage {
  type: MessageType;
  room_id: string;
  payload?: Record<string, unknown>;
}

export interface CallState {
  roomId: string;
  status: CallStatus;
  role: PeerRole | null;
  localStream: MediaStream | null;
  remoteStream: MediaStream | null;
}
