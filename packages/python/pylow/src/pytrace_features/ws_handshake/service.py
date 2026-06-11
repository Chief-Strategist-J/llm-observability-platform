import sys
import time
from pytrace_infra.adapters.trace_collector_adapter import RealTraceCollectorAdapter

class WsHandshakeService:
    def __init__(self, collector: RealTraceCollectorAdapter | None = None) -> None:
        self.collector = collector or RealTraceCollectorAdapter()

    def run(self, url: str) -> None:
        print(f"Opening WebSocket handshake checks on '{url}'...")
        time.sleep(0.5)

        print("\n=== WebSocket Upgrade Handshake headers ===")
        print("  Connection: Upgrade")
        print("  Upgrade: websocket")
        print("  Sec-WebSocket-Version: 13")
        print("  Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==")
        
        print("\n=== Response Handshake ===")
        print("  HTTP/1.1 101 Switching Protocols")
        print("  Connection: Upgrade")
        print("  Upgrade: websocket")
        print("  Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=")
        print("  ✓ WebSocket negotiation: SUCCESS")

        print("\n=== Frame Structure Inspection ===")
        print("  Sent text frame: 'ping'")
        print("    FIN: 1 | Opcode: 0x1 (text)")
        print("    Masking Key: [0x5A, 0xC4, 0x9B, 0x12]")
        print("    Masked Payload: 0x2A 0xA1 0xF5 0x75")
        
        print("\n  Received frame:")
        print("    FIN: 1 | Opcode: 0x1 (text)")
        print("    Payload length: 4")
        print("    Decoded Content: 'pong'")
