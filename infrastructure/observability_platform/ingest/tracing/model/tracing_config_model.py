from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class TracingConfig:
    sampler_type: str = "probabilistic"
    sampler_param: float = 1.0
    collection_interval: str = "5s"
    batch_size: int = 512
    export_timeout: str = "30s"
    exporters: List[str] = field(default_factory=lambda: ["jaeger", "otlp"])
    processors: List[str] = field(default_factory=lambda: ["batch", "memory_limiter"])
    jaeger_host: str = "jaeger-development"
    jaeger_port: int = 6831
    otel_endpoint: str = "http://otel-collector:4317"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sampler_type": self.sampler_type,
            "sampler_param": self.sampler_param,
            "collection_interval": self.collection_interval,
            "batch_size": self.batch_size,
            "export_timeout": self.export_timeout,
            "exporters": self.exporters,
            "processors": self.processors,
            "jaeger_host": self.jaeger_host,
            "jaeger_port": self.jaeger_port,
            "otel_endpoint": self.otel_endpoint
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TracingConfig":
        return cls(
            sampler_type=data.get("sampler_type", "probabilistic"),
            sampler_param=data.get("sampler_param", 1.0),
            collection_interval=data.get("collection_interval", "5s"),
            batch_size=data.get("batch_size", 512),
            export_timeout=data.get("export_timeout", "30s"),
            exporters=data.get("exporters", ["jaeger", "otlp"]),
            processors=data.get("processors", ["batch", "memory_limiter"]),
            jaeger_host=data.get("jaeger_host", "jaeger-development"),
            jaeger_port=data.get("jaeger_port", 6831),
            otel_endpoint=data.get("otel_endpoint", "http://otel-collector:4317")
        )
