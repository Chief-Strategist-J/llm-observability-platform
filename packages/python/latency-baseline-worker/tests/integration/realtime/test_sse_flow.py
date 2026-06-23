import pytest
import http.server
import socketserver
import threading
import json
import time
from realtime.connection.manager import ConnectionManager
from realtime.sse.client import SSEClient
from realtime.sse.types import SSEEvent
from realtime.retry.policy import RetryPolicy

class MockSSEServerHandler(http.server.BaseHTTPRequestHandler):
    recorded_events = []

    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(b"event: checkpoint_created\ndata: {\"ok\": true}\n\n")

    def do_POST(self) -> None:
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        event_dict = json.loads(post_data.decode("utf-8"))
        MockSSEServerHandler.recorded_events.append(event_dict)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok", "id": "event-111"}')

    def log_message(self, format, *args) -> None:
        pass

@pytest.mark.asyncio
async def test_sse_flow_integration() -> None:
    # Set up a random port local server
    handler = MockSSEServerHandler
    handler.recorded_events = []
    
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    try:
        url = f"http://127.0.0.1:{port}"
        
        client = SSEClient()
        manager = ConnectionManager(client=client)
        
        # Connect
        connected = await manager.connect(url)
        assert connected is True
        
        # Push event (simulating activity completion)
        event = SSEEvent(
            event_type="checkpoint_created",
            data={"median": 20.0},
            workflow_id="wf-123",
            run_id="run-456",
            attempt=1
        )
        
        pushed = manager.send_event(url, event)
        assert pushed is True
        
        # Verify the server received the event and workflow_id, run_id are present
        assert len(handler.recorded_events) == 1
        rec = handler.recorded_events[0]
        # Rules: "sse-flow.test must assert workflow ID and run ID are present on every event pushed"
        assert "workflow_id" in rec
        assert rec["workflow_id"] == "wf-123"
        assert "run_id" in rec
        assert rec["run_id"] == "run-456"
        assert rec["attempt"] == 1
        
        # Disconnect
        manager.disconnect()
        assert manager.state.value == "closed"
        
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join()
