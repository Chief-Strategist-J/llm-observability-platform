from features.score_semantic_coherence.rules import THRESHOLDS, classify_coherence


def test_chat_above_threshold() -> None:
    assert classify_coherence(0.30, "chat") == "OK"


def test_chat_below_threshold() -> None:
    assert classify_coherence(0.29, "chat") == "LOW_COHERENCE"


def test_code_above_threshold() -> None:
    assert classify_coherence(0.15, "code") == "OK"


def test_code_below_threshold() -> None:
    assert classify_coherence(0.14, "code") == "LOW_COHERENCE"


def test_rag_above_threshold() -> None:
    assert classify_coherence(0.25, "rag") == "OK"


def test_rag_below_threshold() -> None:
    assert classify_coherence(0.24, "rag") == "LOW_COHERENCE"


def test_classification_above_threshold() -> None:
    assert classify_coherence(0.40, "classification") == "OK"


def test_classification_below_threshold() -> None:
    assert classify_coherence(0.39, "classification") == "LOW_COHERENCE"


def test_thresholds_dict_contains_all_types() -> None:
    assert set(THRESHOLDS.keys()) == {"chat", "code", "rag", "classification"}
