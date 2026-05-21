import os
import tempfile
import pytest
from src.features.pii_injection_scan.infra.adapters.aho_corasick import AhoCorasickNode, AhoCorasickAutomaton
from src.features.pii_injection_scan.infra.adapters.aho_corasick_scanner_adapter import AhoCorasickScannerAdapter
from src.features.manual_instrumentation.service import LLMSpanContext
from src import scan_prompt

@pytest.fixture(autouse=True)
def mock_should_sample():
    from unittest.mock import patch
    with patch("src.features.deterministic_sampling.index.should_sample", return_value=True):
        yield

def test_aho_corasick_basic_match():
    automaton = AhoCorasickAutomaton()
    automaton.add_keyword("forbidden", "FORBIDDEN_TOPIC")
    automaton.add_keyword("jailbreak", "JAILBREAK_PHRASE")
    automaton.build()
    
    res = automaton.search("some text with forbidden words and jailbreak attempts")
    
    assert "FORBIDDEN_TOPIC" in res
    assert "JAILBREAK_PHRASE" in res

def test_aho_corasick_case_insensitive():
    automaton = AhoCorasickAutomaton()
    automaton.add_keyword("forbidden", "FORBIDDEN_TOPIC")
    automaton.build()
    
    res = automaton.search("FoRbIdDeN")
    
    assert "FORBIDDEN_TOPIC" not in res
    
    res_lower = automaton.search("forbidden")
    assert "FORBIDDEN_TOPIC" in res_lower

def test_scanner_adapter_local_yaml():
    adapter = AhoCorasickScannerAdapter()
    
    pii, inj = adapter.scan("test email@example.com address")
    
    assert pii is True
    assert inj is False

def test_scan_prompt_public_api():
    pii, inj = scan_prompt("select * from users")
    
    assert pii is False
    assert inj is True

def test_scan_prompt_message_list():
    messages = [
        {"role": "user", "content": "hello email@example.com"},
        {"role": "assistant", "content": "hi"}
    ]
    
    pii, inj = scan_prompt(messages)
    
    assert pii is True
    assert inj is False

def test_span_context_pii_redaction():
    with LLMSpanContext(prompt="test email@example.com", prompt_hash="old_hash", prompt_embedding=[1, 2]) as span:
        data = span._data
        
    assert data["pii_detected"] is True
    assert data["injection_attempt"] is False
    assert data["prompt"] is None
    assert data["prompt_hash"] is None
    assert data["prompt_embedding"] is None

def test_span_context_injection_flag():
    with LLMSpanContext(prompt="drop table users", prompt_hash="old_hash") as span:
        data = span._data
        
    assert data["pii_detected"] is False
    assert data["injection_attempt"] is True
    assert data["prompt"] == "drop table users"
    assert data["prompt_hash"] == "old_hash"

def test_scanner_handles_none_and_invalid_types():
    assert scan_prompt(None) == (False, False)
    assert scan_prompt(123) == (False, False)
    assert scan_prompt([]) == (False, False)
    assert scan_prompt([{}]) == (False, False)
    assert scan_prompt([{"content": 123}]) == (False, False)
    assert scan_prompt([{"content": [{"type": "text", "text": None}]}]) == (False, False)
    assert scan_prompt([{"content": [{"type": "image", "image_url": "test"}]}]) == (False, False)

def test_scanner_exception_does_not_break_span_init():
    from unittest.mock import patch
    with patch("src.features.pii_injection_scan.index.scan_prompt", side_effect=ValueError("Scanner exploded")):
        with LLMSpanContext(prompt="test email@example.com", prompt_hash="old_hash") as span:
            data = span._data
    assert data["prompt"] == "test email@example.com"
    assert data["pii_detected"] is False

def test_scanner_case_insensitive_and_unicode():
    assert scan_prompt("EMAIL@EXAMPLE.COM") == (True, False)
    assert scan_prompt("Drop Table Users 🧪") == (False, True)

def test_overlapping_matches():
    pii, inj = scan_prompt("test email@example.com and select * from users")
    assert pii is True
    assert inj is True

def test_set_metadata_pii_redaction():
    with LLMSpanContext(prompt="hello world", prompt_hash="old_hash", prompt_embedding=[1]) as span:
        span.set_metadata("prompt", "my email is test@example.com")
        data = span._data
    assert data["pii_detected"] is True
    assert data["prompt"] is None
    assert data["prompt_hash"] is None
    assert data["prompt_embedding"] is None

def test_set_metadata_exception_robustness():
    from unittest.mock import patch
    with LLMSpanContext(prompt="hello world") as span:
        with patch("src.features.pii_injection_scan.index.scan_prompt", side_effect=ValueError("Scanner exploded")):
            span.set_metadata("prompt", "my email is test@example.com")
            data = span._data
    assert data["prompt"] == "my email is test@example.com"
    assert data["pii_detected"] is False
