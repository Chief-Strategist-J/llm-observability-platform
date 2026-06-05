from __future__ import annotations

from core.domain.service import score_nli
from core.domain.types import NliInput

class DummyScorer:
    def __init__(self, token_count: int = 100):
        self.model_id = "dummy-nli"
        self.device_name = "cpu"
        self._token_count = token_count
        self.score_pairs_calls = []

    def count_tokens(self, text: str) -> int:
        return self._token_count

    def split_context_by_tokens(self, text: str, max_tokens: int = 400) -> list[str]:
        return ["chunk1", "chunk2", "chunk3"]

    def score_pairs(
        self,
        pairs: list[tuple[str, str]],
        temperature: float = 1.5,
        batch_size: int = 8,
    ) -> list[tuple[float, float, float]]:
        self.score_pairs_calls.append(pairs)
        res = []
        for prem, hyp in pairs:
            if prem == "chunk2" and hyp == "s1":
                res.append((0.9, 0.05, 0.05))
            elif hyp == "s1":
                res.append((0.2, 0.1, 0.7))
            elif hyp == "s2":
                res.append((0.1, 0.1, 0.8))
            else:
                res.append((0.1, 0.8, 0.1))
        return res

def test_service_without_chunking():
    scorer = DummyScorer(token_count=200)
    inp = NliInput(
        context="simple context",
        sentences=["s1", "s2"],
        temperature=1.2
    )
    result = score_nli(inp, scorer)
    
    assert len(scorer.score_pairs_calls) == 1
    assert len(scorer.score_pairs_calls[0]) == 2
    assert scorer.score_pairs_calls[0] == [("simple context", "s1"), ("simple context", "s2")]
    
    assert result.results[0].sentence == "s1"
    assert result.results[0].label == "contradiction"
    assert result.results[1].label == "contradiction"
    assert result.faithfulness_score == 0.0
    assert set(result.flagged_sentences) == {"s1", "s2"}

def test_service_with_chunking():
    scorer = DummyScorer(token_count=500)
    inp = NliInput(
        context="long context",
        sentences=["s1", "s2"],
        temperature=1.5
    )
    result = score_nli(inp, scorer)
    
    assert len(scorer.score_pairs_calls) == 1
    assert len(scorer.score_pairs_calls[0]) == 6
    
    assert result.results[0].sentence == "s1"
    assert result.results[0].label == "entailment"
    assert result.results[0].probabilities.entailment == 0.9

    assert result.results[1].sentence == "s2"
    assert result.results[1].label == "contradiction"
    
    assert result.faithfulness_score == 0.5
    assert result.flagged_sentences == ["s2"]
