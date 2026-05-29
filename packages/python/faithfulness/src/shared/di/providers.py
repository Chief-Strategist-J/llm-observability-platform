from __future__ import annotations

import os

from infra.adapters.nli.deberta_nli_adapter import DeBertaNliAdapter
from infra.adapters.sentencizer.spacy_sentencizer import SpacySentencizerAdapter


def build_nli_scorer() -> DeBertaNliAdapter:
    model_id = os.environ.get(
        "NLI_MODEL_ID",
        "cross-encoder/nli-deberta-v3-base",
    )
    return DeBertaNliAdapter(model_id=model_id)


def build_sentencizer() -> SpacySentencizerAdapter:
    model_name = os.environ.get("SPACY_MODEL", "en_core_web_sm")
    return SpacySentencizerAdapter(model_name=model_name)
