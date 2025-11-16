import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TraceDiscoveryService:
    def __init__(self):
        self.discovered_sources = []

    def discover_sources(self) -> List[Dict[str, Any]]:
        try:
            sources = [
                {
                    "name": "jaeger",
                    "type": "jaeger",
                    "url": "http://jaeger-development:16686",
                    "enabled": True
                },
                {
                    "name": "otel-collector",
                    "type": "otlp",
                    "url": "http://otel-collector:4317",
                    "enabled": True
                }
            ]
            self.discovered_sources = sources
            logger.info("Discovered %d trace sources", len(sources))
            return sources
        except Exception as e:
            logger.error("Error discovering trace sources: %s", str(e))
            return []

    def get_source_config(self, source_name: str) -> Dict[str, Any]:
        for source in self.discovered_sources:
            if source.get("name") == source_name:
                return source
        return {}

    def validate_source(self, source: Dict[str, Any]) -> bool:
        required_fields = ["name", "type", "url"]
        return all(field in source for field in required_fields)
