import type { SignalMessage } from "@features/call/types";

export interface ISignalingPort {
  connect(roomId: string): void;
  send(message: SignalMessage): void;
  onMessage(callback: (message: SignalMessage) => void): void;
  onOpen(callback: () => void): void;
  onClose(callback: () => void): void;
  disconnect(): void;
}
