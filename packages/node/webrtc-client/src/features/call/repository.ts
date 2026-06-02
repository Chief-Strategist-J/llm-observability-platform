import type { ISignalingPort } from "@ports/signaling_port";
import type { SignalMessage } from "./types";

export class SignalingRepository implements ISignalingPort {
  private ws: WebSocket | null = null;
  private messageCallback: ((msg: SignalMessage) => void) | null = null;
  private openCallback: (() => void) | null = null;
  private closeCallback: (() => void) | null = null;
  private readonly baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  connect(roomId: string): void {
    const url = `${this.baseUrl}/ws/${encodeURIComponent(roomId)}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.openCallback?.();
    };

    this.ws.onmessage = (event: MessageEvent<string>) => {
      const data = JSON.parse(event.data) as SignalMessage;
      this.messageCallback?.(data);
    };

    this.ws.onclose = () => {
      this.closeCallback?.();
    };
  }

  send(message: SignalMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  onMessage(callback: (message: SignalMessage) => void): void {
    this.messageCallback = callback;
  }

  onOpen(callback: () => void): void {
    this.openCallback = callback;
  }

  onClose(callback: () => void): void {
    this.closeCallback = callback;
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }
}
