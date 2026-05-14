import hashlib


def stable_embedding_key(trace_id: str, span_id: str, text: str, prefix: str = "emb_") -> str:
    digest_source = f"{trace_id}:{span_id}:{text}".encode("utf-8")
    digest = hashlib.sha256(digest_source).hexdigest()[:24]
    return f"{prefix}{digest}"
