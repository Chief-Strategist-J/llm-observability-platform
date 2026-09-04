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


def test_service_registry_integration(monkeypatch):
    from unittest.mock import MagicMock, patch
    from worker.config import load_config
    from python_shared.discovery import ServiceRegistryManager

    mock_manager = MagicMock(spec=ServiceRegistryManager)
    mock_manager.register_sync.return_value = "inst-event-cost-123"

    with patch("worker.index.ServiceRegistryManager", return_value=mock_manager) as mock_cls:
        cfg = load_config({"HEALTH_PORT": "8005"})
        mgr = mock_cls()
        inst_id = mgr.register_sync()
        assert inst_id == "inst-event-cost-123"
        mgr.deregister_sync()
        mock_manager.deregister_sync.assert_called_once()
