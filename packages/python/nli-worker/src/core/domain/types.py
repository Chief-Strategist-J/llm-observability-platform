from __future__ import annotations

from pydantic import BaseModel

class NliInput(BaseModel):
    context: str
    sentences: list[str]
    temperature: float = 1.5

class SentenceProbability(BaseModel):
    entailment: float
    neutral: float
    contradiction: float

class SentenceResult(BaseModel):
    sentence: str
    label: str
    probabilities: SentenceProbability

class NliResult(BaseModel):
    results: list[SentenceResult]
    faithfulness_score: float
    flagged_sentences: list[str]
