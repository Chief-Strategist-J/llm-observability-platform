export interface IMediaPort {
  getLocalStream(constraints: MediaStreamConstraints): Promise<MediaStream>;
  attachLocalStream(stream: MediaStream, element: HTMLVideoElement): void;
  attachRemoteStream(stream: MediaStream, element: HTMLVideoElement): void;
  stopStream(stream: MediaStream): void;
}
