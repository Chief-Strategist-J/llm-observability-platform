from __future__ import annotations

import os

from infra.adapters.gpt2.gpt2_onnx_adapter import Gpt2OnnxAdapter
from infra.adapters.logprobs.provider_logprobs_adapter import ProviderLogprobsAdapter


def build_logprobs_scorer() -> ProviderLogprobsAdapter:
    return ProviderLogprobsAdapter()


def build_gpt2_scorer() -> Gpt2OnnxAdapter:
    model_path = os.environ.get("GPT2_MODEL_PATH", "gpt2")
    return Gpt2OnnxAdapter(model_path=model_path)
