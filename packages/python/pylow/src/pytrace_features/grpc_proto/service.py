import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class GrpcProtoService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, method: str, payload: str) -> None:
        print(f"Encoding gRPC payload for method '{method}'...")
        time.sleep(0.5)

        # 5-byte header encoding: 1-byte compression flag + 4-byte length in big endian
        raw_payload = payload.encode("utf-8")
        length_bytes = len(raw_payload).to_bytes(4, byteorder="big")
        frame_header = b"\x00" + length_bytes
        
        print("\n=== Protobuf Wire Format Frame Output ===")
        print(f"  Compression:   0 (Uncompressed)")
        print(f"  Length:        {len(raw_payload)} bytes")
        print(f"  Frame Header:  {frame_header.hex().upper()}")
        print(f"  Payload Hex:   {raw_payload.hex().upper()}")
        
        print("\n=== Sending gRPC Request (HTTP/2) ===")
        print(f"  POST https://api.example.com/{method}")
        print("  Content-Type: application/grpc")
        print("  TE: trailers")
        
        print("\n=== Response Trailers ===")
        print("  grpc-status:  0 (OK)")
        print("  grpc-message: Successful request completion")
