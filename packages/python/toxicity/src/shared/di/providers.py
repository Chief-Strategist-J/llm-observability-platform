from __future__ import annotations

import os

from infra.adapters.detoxify_onnx_adapter import DetoxifyOnnxAdapter
from infra.adapters.kafka_publisher_adapter import KafkaToxicityPublisherAdapter

def build_toxicity_scorer() -> DetoxifyOnnxAdapter:
    model_id = os.environ.get("TOXICITY_MODEL_ID", "unitary/toxic-bert")
    return DetoxifyOnnxAdapter(model_id=model_id)

def build_toxicity_publisher() -> KafkaToxicityPublisherAdapter:
    bootstrap_servers = os.environ.get("KAFKA_BOOTSTRAP_SERVERS")
    return KafkaToxicityPublisherAdapter(bootstrap_servers=bootstrap_servers)
