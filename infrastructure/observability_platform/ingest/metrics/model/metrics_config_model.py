from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class MetricsConfig:
    scrape_interval: str = "15s"
    evaluation_interval: str = "15s"
    collection_interval: str = "15s"
    batch_size: int = 100
    export_timeout: str = "30s"
    exporters: List[str] = field(default_factory=lambda: ["prometheus", "otlp"])
    scrape_configs: List[Dict[str, Any]] = field(default_factory=list)
    remote_write: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scrape_interval": self.scrape_interval,
            "evaluation_interval": self.evaluation_interval,
            "collection_interval": self.collection_interval,
            "batch_size": self.batch_size,
            "export_timeout": self.export_timeout,
            "exporters": self.exporters,
            "scrape_configs": self.scrape_configs,
            "remote_write": self.remote_write
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricsConfig":
        return cls(
            scrape_interval=data.get("scrape_interval", "15s"),
            evaluation_interval=data.get("evaluation_interval", "15s"),
            collection_interval=data.get("collection_interval", "15s"),
            batch_size=data.get("batch_size", 100),
            export_timeout=data.get("export_timeout", "30s"),
            exporters=data.get("exporters", ["prometheus", "otlp"]),
            scrape_configs=data.get("scrape_configs", []),
            remote_write=data.get("remote_write", [])
        )
