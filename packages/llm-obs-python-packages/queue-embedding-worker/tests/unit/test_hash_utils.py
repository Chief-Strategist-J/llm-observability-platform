from shared.utils.hash import stable_embedding_key


def test_stable_embedding_key_prefix_default():
    key = stable_embedding_key("t", "s", "x")
    assert key.startswith("emb_")


def test_stable_embedding_key_prefix_custom():
    key = stable_embedding_key("t", "s", "x", prefix="k_")
    assert key.startswith("k_")


def test_stable_embedding_key_is_deterministic():
    assert stable_embedding_key("t", "s", "x") == stable_embedding_key("t", "s", "x")


def test_stable_embedding_key_changes_on_trace_id():
    assert stable_embedding_key("t1", "s", "x") != stable_embedding_key("t2", "s", "x")


def test_stable_embedding_key_changes_on_span_id():
    assert stable_embedding_key("t", "s1", "x") != stable_embedding_key("t", "s2", "x")


def test_stable_embedding_key_has_expected_length():
    key = stable_embedding_key("t", "s", "x")
    assert len(key) == 4 + 24
