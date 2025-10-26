# Service package

from pathlib import Path
import sys

# Add the service directory to Python path
service_dir = Path(__file__).parent
if str(service_dir) not in sys.path:
    sys.path.insert(0, str(service_dir))

# Simple aliases for service directories with hyphens
import types

# kg-service
kg_service = types.ModuleType("kg_service")
kg_service.__path__ = [str(service_dir / "kg-service")]
sys.modules["service.kg_service"] = kg_service

# ai-proxy-service
ai_proxy_service = types.ModuleType("ai_proxy_service")
ai_proxy_service.__path__ = [str(service_dir / "ai-proxy-service")]
sys.modules["service.ai_proxy_service"] = ai_proxy_service

# rag-service
rag_service = types.ModuleType("rag_service")
rag_service.__path__ = [str(service_dir / "rag-service")]
sys.modules["service.rag_service"] = rag_service

# automation-n8n-service
automation_n8n_service = types.ModuleType("automation_n8n_service")
automation_n8n_service.__path__ = [str(service_dir / "automation-n8n-service")]
sys.modules["service.automation_n8n_service"] = automation_n8n_service

# redis-service (standalone module)
redis_service = types.ModuleType("redis_service")
redis_service.__path__ = [str(service_dir)]
sys.modules["service.redis_service"] = redis_service

# telemetry (standalone module)
telemetry = types.ModuleType("telemetry")
telemetry.__path__ = [str(service_dir)]
sys.modules["service.telemetry"] = telemetry
