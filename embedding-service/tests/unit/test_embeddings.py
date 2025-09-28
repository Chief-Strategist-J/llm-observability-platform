"""Test embedding functionality."""
import pytest
from services.embedding.text_embedder import TextEmbedder

def test_text_embedder():
    embedder = TextEmbedder("demo", 384)
    vector = embedder.embed("test text")
    assert len(vector) == 384
    assert all(isinstance(v, float) for v in vector)

def test_consistent_embeddings():
    embedder = TextEmbedder("demo", 384)
    text = "consistent test"
    vec1 = embedder.embed(text)
    vec2 = embedder.embed(text)
    assert vec1 == vec2
