from http.server import HTTPServer
import threading
import urllib.request
import json

from worker.index import _HealthHandler

def test_health_handler():
    server = HTTPServer(("127.0.0.1", 0), _HealthHandler)
    port = server.server_port
    
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    
    try:
        url = f"http://127.0.0.1:{port}/health"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            assert data == {"status": "ok"}
            assert resp.status == 200
    finally:
        server.shutdown()
        server.server_close()
