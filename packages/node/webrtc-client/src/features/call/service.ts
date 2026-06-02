import type { IMediaPort } from "@ports/media_port";
import type { ISignalingPort } from "@ports/signaling_port";
import type { CallState, PeerRole, SignalMessage } from "./types";

export class CallService {
  private state: CallState;
  private peerConnection: RTCPeerConnection | null = null;

  constructor(
    private readonly signaling: ISignalingPort,
    private readonly media: IMediaPort,
    private readonly roomId: string,
    private readonly iceServers: RTCIceServer[],
    private readonly onStateChange: (state: CallState) => void
  ) {
    this.state = {
      roomId,
      status: "idle",
      role: null,
      localStream: null,
      remoteStream: null,
    };
  }

  async start(): Promise<void> {
    const stream = await this.media.getLocalStream({ video: true, audio: true });
    this.setState({ localStream: stream, status: "connecting" });

    this.signaling.onOpen(() => this.setState({ status: "waiting-for-peer" }));
    this.signaling.onClose(() => this.setState({ status: "disconnected" }));
    this.signaling.onMessage((msg) => this._handleSignal(msg));
    this.signaling.connect(this.roomId);
  }

  stop(): void {
    this.peerConnection?.close();
    this.peerConnection = null;
    if (this.state.localStream) {
      this.media.stopStream(this.state.localStream);
    }
    this.signaling.disconnect();
    this.setState({ status: "disconnected", localStream: null, remoteStream: null, role: null });
  }

  private async _handleSignal(message: SignalMessage): Promise<void> {
    switch (message.type) {
      case "peer-joined":
        await this._startAsOfferer();
        break;
      case "offer":
        await this._handleOffer(message);
        break;
      case "answer":
        await this._handleAnswer(message);
        break;
      case "ice-candidate":
        await this._handleIceCandidate(message);
        break;
      case "peer-left":
        this.setState({ status: "disconnected" });
        break;
    }
  }

  private _createPeerConnection(role: PeerRole): RTCPeerConnection {
    const pc = new RTCPeerConnection({ iceServers: this.iceServers });
    this.setState({ role });

    this.state.localStream?.getTracks().forEach((track) => {
      pc.addTrack(track, this.state.localStream!);
    });

    pc.ontrack = (event: RTCTrackEvent) => {
      const remoteStream = event.streams[0] ?? new MediaStream([event.track]);
      this.setState({ remoteStream });
    };

    pc.onicecandidate = (event: RTCPeerConnectionIceEvent) => {
      if (event.candidate) {
        this.signaling.send({
          type: "ice-candidate",
          room_id: this.roomId,
          payload: event.candidate.toJSON() as Record<string, unknown>,
        });
      }
    };

    pc.onconnectionstatechange = () => {
      if (pc.connectionState === "connected") {
        this.setState({ status: "connected" });
      } else if (pc.connectionState === "failed" || pc.connectionState === "closed") {
        this.setState({ status: "error" });
      }
    };

    return pc;
  }

  private async _startAsOfferer(): Promise<void> {
    this.setState({ status: "negotiating" });
    this.peerConnection = this._createPeerConnection("offerer");

    const offer = await this.peerConnection.createOffer();
    await this.peerConnection.setLocalDescription(offer);
    this.signaling.send({
      type: "offer",
      room_id: this.roomId,
      payload: { sdp: offer.sdp, type: offer.type },
    });
  }

  private async _handleOffer(message: SignalMessage): Promise<void> {
    this.setState({ status: "negotiating" });
    this.peerConnection = this._createPeerConnection("answerer");

    const sdpInit = message.payload as unknown as RTCSessionDescriptionInit;
    await this.peerConnection.setRemoteDescription(new RTCSessionDescription(sdpInit));

    const answer = await this.peerConnection.createAnswer();
    await this.peerConnection.setLocalDescription(answer);
    this.signaling.send({
      type: "answer",
      room_id: this.roomId,
      payload: { sdp: answer.sdp, type: answer.type },
    });
  }

  private async _handleAnswer(message: SignalMessage): Promise<void> {
    const sdpInit = message.payload as unknown as RTCSessionDescriptionInit;
    await this.peerConnection?.setRemoteDescription(new RTCSessionDescription(sdpInit));
  }

  private async _handleIceCandidate(message: SignalMessage): Promise<void> {
    if (message.payload && this.peerConnection) {
      const candidate = new RTCIceCandidate(message.payload as RTCIceCandidateInit);
      await this.peerConnection.addIceCandidate(candidate);
    }
  }

  private setState(partial: Partial<CallState>): void {
    this.state = { ...this.state, ...partial };
    this.onStateChange(this.state);
  }
}
