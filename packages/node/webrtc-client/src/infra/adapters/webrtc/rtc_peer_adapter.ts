import type { IMediaPort } from "@ports/media_port";

export class BrowserMediaAdapter implements IMediaPort {
  async getLocalStream(constraints: MediaStreamConstraints): Promise<MediaStream> {
    return navigator.mediaDevices.getUserMedia(constraints);
  }

  attachLocalStream(stream: MediaStream, element: HTMLVideoElement): void {
    element.srcObject = stream;
    element.muted = true;
    void element.play();
  }

  attachRemoteStream(stream: MediaStream, element: HTMLVideoElement): void {
    element.srcObject = stream;
    void element.play();
  }

  stopStream(stream: MediaStream): void {
    stream.getTracks().forEach((track) => track.stop());
  }
}
