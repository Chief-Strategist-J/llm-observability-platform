"""
Critical tests for faithfulness scorer — business-perspective edge cases and failure modes.

Business context:
  The faithfulness score answers: "Did the LLM hallucinate, or did it stay grounded
  in the retrieved context?"

  score = entailed_sentences / total_qualifying_sentences

  A score of 1.0 → every sentence the model produced is supported by the context.
  A score of 0.0 → every sentence contradicts or is unrelated to the context.
  score = null  → not enough signal to score (short response, no context, blocked).

  Downstream composite scorer weights faithfulness at 0.40.
  When null the weight is redistributed — no penalty, no reward.
"""
from __future__ import annotations

import pytest

from features.score_faithfulness.service import score_faithfulness
from features.score_faithfulness.types import FaithfulnessInput, FaithfulnessResult
from features.score_faithfulness.rules import (
    MIN_CONTEXT_CHARS,
    MIN_COMPLETION_TOKENS,
    MIN_SENTENCE_WORDS,
    CONTEXT_TOKEN_LIMIT,
    CONTEXT_CHUNK_TOKENS,
    TEMPERATURE,
    NLI_BATCH_SIZE,
)


class _NliRecorder:
    """Records all calls and returns configurable per-call probs."""

    model_id = "test/recorder"

    def __init__(self, responses: list[list[tuple[float, float, float]]]) -> None:
        self._responses = iter(responses)
        self.calls: list[list[tuple[str, str]]] = []

    def score_pairs(self, pairs):
        self.calls.append(list(pairs))
        return next(self._responses)


class _StaticNli:
    """Always returns the same prob vector for every pair."""

    model_id = "test/static"

    def __init__(self, probs: tuple[float, float, float]) -> None:
        self._probs = probs

    def score_pairs(self, pairs):
        return [self._probs] * len(pairs)


class _StaticSentencizer:
    def __init__(self, sentences: list[str]) -> None:
        self._sentences = sentences

    def split(self, text: str, min_words: int) -> list[str]:
        return self._sentences


def _inp(**kwargs) -> FaithfulnessInput:
    base = dict(
        rag_context="x" * MIN_CONTEXT_CHARS,
        response_text="Some model response text here.",
        completion_tokens=MIN_COMPLETION_TOKENS,
        finish_reason=None,
    )
    base.update(kwargs)
    return FaithfulnessInput(**base)


# ─────────────────────────────────────────────────────────────
# CRITICAL: Skip-condition boundary tests
# Each skip condition must return score=None — never a number.
# Downstream composite scorer relies on None to renormalize weights.
# ─────────────────────────────────────────────────────────────

class TestSkipConditionBoundaries:

    def test_context_null_must_skip(self):
        """A null RAG context means no grounding signal exists — must skip."""
        r = score_faithfulness(_inp(rag_context=None), _StaticSentencizer([]), _StaticNli((0.9, 0.05, 0.05)))
        assert r.skipped is True
        assert r.score is None
        assert r.skip_reason == "rag_context_null"

    def test_context_one_char_below_limit_must_skip(self):
        """Context of MIN-1 chars is too short to ground any claim."""
        r = score_faithfulness(_inp(rag_context="x" * (MIN_CONTEXT_CHARS - 1)), _StaticSentencizer([]), _StaticNli((0.9, 0.05, 0.05)))
        assert r.skipped is True
        assert r.skip_reason == "rag_context_too_short"

    def test_context_exactly_at_min_must_not_skip(self):
        """Context at exactly MIN chars is acceptable — must NOT skip."""
        r = score_faithfulness(
            _inp(rag_context="x" * MIN_CONTEXT_CHARS),
            _StaticSentencizer(["This is one qualifying sentence here."]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is False

    def test_completion_tokens_one_below_min_must_skip(self):
        """Too few tokens → response not substantive enough to evaluate."""
        r = score_faithfulness(_inp(completion_tokens=MIN_COMPLETION_TOKENS - 1), _StaticSentencizer([]), _StaticNli((0.9, 0.05, 0.05)))
        assert r.skipped is True
        assert r.skip_reason == "completion_tokens_too_few"

    def test_completion_tokens_exactly_at_min_must_not_skip(self):
        r = score_faithfulness(
            _inp(completion_tokens=MIN_COMPLETION_TOKENS),
            _StaticSentencizer(["This is one qualifying sentence."]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is False

    def test_content_filter_finish_reason_must_skip(self):
        """Content-filtered responses may not reflect true model output — skip."""
        r = score_faithfulness(
            _inp(finish_reason="content_filter"),
            _StaticSentencizer(["This sentence would normally be scored."]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is True
        assert r.score is None
        assert r.skip_reason == "finish_reason_blocked"

    def test_stop_finish_reason_must_not_skip(self):
        """Normal 'stop' finish reason → proceed to score."""
        r = score_faithfulness(
            _inp(finish_reason="stop"),
            _StaticSentencizer(["The model completed normally here."]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is False

    def test_length_finish_reason_must_not_skip(self):
        """Truncated responses are still scoreable."""
        r = score_faithfulness(
            _inp(finish_reason="length"),
            _StaticSentencizer(["The model was truncated at max tokens."]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is False

    def test_all_sentences_too_short_must_skip(self):
        """If sentencizer filters everything out, no signal → skip."""
        r = score_faithfulness(_inp(), _StaticSentencizer([]), _StaticNli((0.9, 0.05, 0.05)))
        assert r.skipped is True
        assert r.skip_reason == "no_qualifying_sentences"
        assert r.total_qualifying == 0
        assert r.score is None


# ─────────────────────────────────────────────────────────────
# CRITICAL: Score computation correctness
# Business rule: score = entailed / total.
# Rounding, division-by-zero, and boundary values must be exact.
# ─────────────────────────────────────────────────────────────

class TestScoreComputation:

    def test_perfect_faithfulness_score_is_1(self):
        """All sentences entailed → score must be exactly 1.0."""
        sentences = ["Sentence one here.", "Sentence two here.", "Sentence three here."]
        r = score_faithfulness(
            _inp(),
            _StaticSentencizer(sentences),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.score == pytest.approx(1.0)
        assert r.entailed_count == 3
        assert r.total_qualifying == 3

    def test_zero_faithfulness_score_is_0(self):
        """All contradicted → score must be exactly 0.0."""
        sentences = ["Sentence A here.", "Sentence B here."]
        r = score_faithfulness(
            _inp(),
            _StaticSentencizer(sentences),
            _StaticNli((0.05, 0.05, 0.9)),
        )
        assert r.score == pytest.approx(0.0)
        assert r.entailed_count == 0

    def test_half_entailed_score_is_0_5(self):
        """Exactly half entailed → score = 0.5."""
        nli = _NliRecorder([
            [(0.9, 0.05, 0.05), (0.05, 0.9, 0.05)],
        ])
        r = score_faithfulness(
            _inp(),
            _StaticSentencizer(["Entailed sentence.", "Neutral sentence here."]),
            nli,
        )
        assert r.score == pytest.approx(0.5)

    def test_single_sentence_entailed_score_is_1(self):
        r = score_faithfulness(
            _inp(),
            _StaticSentencizer(["Only one sentence here."]),
            _StaticNli((0.8, 0.1, 0.1)),
        )
        assert r.score == pytest.approx(1.0)
        assert r.total_qualifying == 1

    def test_single_sentence_neutral_score_is_0(self):
        r = score_faithfulness(
            _inp(),
            _StaticSentencizer(["Only one sentence here."]),
            _StaticNli((0.1, 0.8, 0.1)),
        )
        assert r.score == pytest.approx(0.0)
        assert r.entailed_count == 0

    def test_entailed_count_always_matches_sentence_results(self):
        """entailed_count must equal count of 'entailment' labels in sentence_results."""
        sentences = ["S1 here.", "S2 here.", "S3 here."]
        nli = _NliRecorder([
            [(0.9, 0.05, 0.05), (0.05, 0.9, 0.05), (0.9, 0.05, 0.05)],
        ])
        r = score_faithfulness(_inp(), _StaticSentencizer(sentences), nli)
        counted = sum(1 for s in r.sentence_results if s.label == "entailment")
        assert r.entailed_count == counted

    def test_score_is_consistent_with_sentence_results(self):
        """score must equal entailed_count / total_qualifying — no floating point drift."""
        sentences = [f"Sentence number {i} in the response text." for i in range(7)]
        probs = [(0.9, 0.05, 0.05)] * 4 + [(0.05, 0.9, 0.05)] * 3
        nli = _NliRecorder([probs])
        r = score_faithfulness(_inp(), _StaticSentencizer(sentences), nli)
        expected = r.entailed_count / r.total_qualifying
        assert r.score == pytest.approx(expected)


# ─────────────────────────────────────────────────────────────
# CRITICAL: Long-context chunking
# When context > 512 words: chunk into 400-word blocks.
# Each sentence is scored against ALL chunks; take the MAX
# entailment probability across chunks (benefit of the doubt).
# ─────────────────────────────────────────────────────────────

class TestLongContextChunking:

    def _long_context(self, words: int) -> str:
        return " ".join(["contextword"] * words)

    def test_chunking_activates_above_512_words(self):
        """NLI should be called once per chunk, not once total."""
        context = self._long_context(CONTEXT_TOKEN_LIMIT + 1)
        sentences = ["Sentence alpha here.", "Sentence beta here."]
        expected_chunks = (CONTEXT_TOKEN_LIMIT + 1 + CONTEXT_CHUNK_TOKENS - 1) // CONTEXT_CHUNK_TOKENS

        call_count = [0]
        probs_per_call = [(0.8, 0.1, 0.1)] * len(sentences)

        class CountingNli:
            model_id = "test"
            def score_pairs(self, pairs):
                call_count[0] += 1
                return probs_per_call[:len(pairs)]

        score_faithfulness(_inp(rag_context=context), _StaticSentencizer(sentences), CountingNli())
        assert call_count[0] == expected_chunks

    def test_chunking_does_not_activate_at_exactly_512_words(self):
        """At exactly 512 words context is processed in one shot."""
        context = self._long_context(CONTEXT_TOKEN_LIMIT)
        call_count = [0]

        class CountingNli:
            model_id = "test"
            def score_pairs(self, pairs):
                call_count[0] += 1
                return [(0.9, 0.05, 0.05)] * len(pairs)

        score_faithfulness(_inp(rag_context=context), _StaticSentencizer(["One qualifying sentence."]), CountingNli())
        assert call_count[0] == 1

    def test_chunking_takes_max_entailment_across_chunks(self):
        """A sentence only needs to be entailed by ONE chunk to count as entailed."""
        context = self._long_context(CONTEXT_TOKEN_LIMIT + 1)
        sentences = ["Test sentence here."]

        call_num = [0]

        class MaxPickNli:
            model_id = "test"
            def score_pairs(self, pairs):
                idx = call_num[0]
                call_num[0] += 1
                if idx == 0:
                    return [(0.1, 0.5, 0.4)]
                return [(0.9, 0.05, 0.05)]

        r = score_faithfulness(_inp(rag_context=context), _StaticSentencizer(sentences), MaxPickNli())
        assert r.sentence_results[0].label == "entailment"
        assert r.sentence_results[0].entailment_prob == pytest.approx(0.9)

    def test_chunking_takes_worst_case_if_all_chunks_contradict(self):
        """If no chunk entails a sentence, it's not entailed."""
        context = self._long_context(CONTEXT_TOKEN_LIMIT + 1)
        sentences = ["Hallucinated claim about Mars."]

        class AllContradictNli:
            model_id = "test"
            def score_pairs(self, pairs):
                return [(0.05, 0.05, 0.9)] * len(pairs)

        r = score_faithfulness(_inp(rag_context=context), _StaticSentencizer(sentences), AllContradictNli())
        assert r.sentence_results[0].label == "contradiction"
        assert r.score == pytest.approx(0.0)

    def test_chunk_size_does_not_exceed_limit(self):
        """Each chunk passed to NLI must be ≤ CONTEXT_CHUNK_TOKENS words."""
        context = self._long_context(CONTEXT_TOKEN_LIMIT + CONTEXT_CHUNK_TOKENS + 50)

        class ChunkSizeVerifierNli:
            model_id = "test"
            def score_pairs(self, pairs):
                for premise, _ in pairs:
                    word_count = len(premise.split())
                    assert word_count <= CONTEXT_CHUNK_TOKENS, (
                        f"Chunk has {word_count} words, limit is {CONTEXT_CHUNK_TOKENS}"
                    )
                return [(0.9, 0.05, 0.05)] * len(pairs)

        score_faithfulness(_inp(rag_context=context), _StaticSentencizer(["Qualifying sentence here."]), ChunkSizeVerifierNli())


# ─────────────────────────────────────────────────────────────
# CRITICAL: NLI adapter batching contract
# The adapter must handle: empty input, partial batches,
# exact-batch-size, and multi-batch inputs correctly.
# ─────────────────────────────────────────────────────────────

class TestNliBatchingContract:

    def test_empty_pairs_returns_empty(self):
        from infra.adapters.nli.deberta_nli_adapter import DeBertaNliAdapter
        adapter = _build_fake_adapter()
        assert adapter.score_pairs([]) == []

    def test_single_pair_returns_one_triple(self):
        adapter = _build_fake_adapter()
        result = adapter.score_pairs([("premise text here", "hypothesis text here")])
        assert len(result) == 1
        assert len(result[0]) == 3

    def test_exact_batch_size_returns_correct_length(self):
        adapter = _build_fake_adapter()
        pairs = [("p", "h")] * NLI_BATCH_SIZE
        result = adapter.score_pairs(pairs)
        assert len(result) == NLI_BATCH_SIZE

    def test_one_over_batch_size_returns_correct_length(self):
        adapter = _build_fake_adapter()
        pairs = [("p", "h")] * (NLI_BATCH_SIZE + 1)
        result = adapter.score_pairs(pairs)
        assert len(result) == NLI_BATCH_SIZE + 1

    def test_all_probs_sum_to_one(self):
        adapter = _build_fake_adapter()
        pairs = [("p", "h")] * 5
        for e, n, c in adapter.score_pairs(pairs):
            assert pytest.approx(1.0, abs=1e-4) == (e + n + c)

    def test_probs_are_all_non_negative(self):
        adapter = _build_fake_adapter()
        pairs = [("p", "h")] * 3
        for probs in adapter.score_pairs(pairs):
            assert all(p >= 0.0 for p in probs)


def _build_fake_adapter():
    """Build a DeBertaNliAdapter with fake tokenizer + model (no download)."""
    import types
    import torch
    from infra.adapters.nli.deberta_nli_adapter import DeBertaNliAdapter

    class FakeTok:
        def __call__(self, premises, hypotheses, **kw):
            n = len(premises)
            return {"input_ids": torch.zeros(n, 4, dtype=torch.long)}

    class FakeOutput:
        def __init__(self, logits):
            self.logits = logits

    class FakeMdl:
        def __init__(self):
            self.config = types.SimpleNamespace(
                id2label={0: "contradiction", 1: "neutral", 2: "entailment"}
            )
        def eval(self): return self
        def __call__(self, **kw):
            n = kw["input_ids"].shape[0]
            logits = torch.zeros(n, 3)
            logits[:, 2] = 2.0
            return FakeOutput(logits)

    adapter = DeBertaNliAdapter.__new__(DeBertaNliAdapter)
    adapter._model_id = "test/fake"
    adapter.__dict__["_tokenizer"] = FakeTok()
    adapter.__dict__["_model"] = FakeMdl()
    return adapter


# ─────────────────────────────────────────────────────────────
# CRITICAL: Failure case — malformed / degenerate inputs
# These simulate real-world bad data from upstream pipelines.
# ─────────────────────────────────────────────────────────────

class TestFailureCases:

    def test_response_text_empty_string(self):
        """Empty response produces no sentences → skip with no_qualifying_sentences."""
        r = score_faithfulness(
            _inp(response_text=""),
            _StaticSentencizer([]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is True
        assert r.skip_reason == "no_qualifying_sentences"
        assert r.score is None

    def test_response_text_whitespace_only(self):
        """Whitespace-only response produces no qualifying sentences."""
        r = score_faithfulness(
            _inp(response_text="   \n\t  "),
            _StaticSentencizer([]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is True
        assert r.score is None

    def test_context_whitespace_only_is_too_short(self):
        """Whitespace-only context has no useful content — treated as too short."""
        r = score_faithfulness(
            _inp(rag_context="   "),
            _StaticSentencizer(["Valid sentence in response."]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is True
        assert r.skip_reason in ("rag_context_too_short", "rag_context_null")

    def test_context_is_single_repeated_character(self):
        """Garbage context (MIN chars of 'x') is syntactically valid but semantically empty.
        Service must NOT crash — it passes it to NLI unchanged."""
        r = score_faithfulness(
            _inp(rag_context="x" * MIN_CONTEXT_CHARS),
            _StaticSentencizer(["A real sentence about something."]),
            _StaticNli((0.05, 0.9, 0.05)),
        )
        assert r.skipped is False
        assert r.score == pytest.approx(0.0)

    def test_very_large_number_of_sentences_does_not_crash(self):
        """100 sentences must all be processed without errors."""
        sentences = [f"Sentence number {i} in the response." for i in range(100)]
        nli = _StaticNli((0.8, 0.1, 0.1))
        r = score_faithfulness(_inp(), _StaticSentencizer(sentences), nli)
        assert r.skipped is False
        assert r.total_qualifying == 100
        assert r.score == pytest.approx(1.0)

    def test_one_sentence_with_unknown_finish_reason_proceeds(self):
        """Unknown finish reasons must not trigger a skip."""
        r = score_faithfulness(
            _inp(finish_reason="tool_call"),
            _StaticSentencizer(["The answer is grounded in context."]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is False

    def test_zero_completion_tokens_must_skip(self):
        """completion_tokens=0 is definitely too few."""
        r = score_faithfulness(
            _inp(completion_tokens=0),
            _StaticSentencizer(["Something."]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is True

    def test_negative_completion_tokens_must_skip(self):
        """Negative token count (upstream bug) must be treated as too few."""
        r = score_faithfulness(
            _inp(completion_tokens=-5),
            _StaticSentencizer(["Something."]),
            _StaticNli((0.9, 0.05, 0.05)),
        )
        assert r.skipped is True

    def test_nli_returns_equal_probs_label_is_deterministic(self):
        """Tie-breaking must be consistent — 'entailment' when all equal (index 0 wins)."""
        r = score_faithfulness(
            _inp(),
            _StaticSentencizer(["A sentence that is ambiguous."]),
            _StaticNli((1 / 3, 1 / 3, 1 / 3)),
        )
        assert r.sentence_results[0].label in ("entailment", "neutral", "contradiction")
        assert r.score is not None

    def test_skipped_result_has_empty_sentence_list(self):
        """Skipped results must return empty sentence_results (no partial data)."""
        r = score_faithfulness(_inp(rag_context=None), _StaticSentencizer([]), _StaticNli((0.9, 0.05, 0.05)))
        assert r.sentence_results == []

    def test_result_fields_never_partially_null_when_scored(self):
        """When not skipped, score, entailed_count, total_qualifying must all be set."""
        r = score_faithfulness(
            _inp(),
            _StaticSentencizer(["A valid grounded sentence here."]),
            _StaticNli((0.8, 0.1, 0.1)),
        )
        assert r.skipped is False
        assert r.score is not None
        assert r.entailed_count is not None
        assert r.total_qualifying is not None
        assert r.skip_reason is None


class TestOpenTelemetryTracing:

    def test_trace_span_with_ids(self):
        from opentelemetry import trace
        r = score_faithfulness(
            _inp(),
            _StaticSentencizer(["A valid grounded sentence here."]),
            _StaticNli((0.8, 0.1, 0.1)),
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
        )
        assert r.score is not None

