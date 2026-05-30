import pytest
from smartchunker.tokenizers import (
    WordCountTokenizer,
    TiktokenTokenizer,
    HFTokenizer,
    resolve_tokenizer
)

def test_word_count_tokenizer():
    tokenizer = WordCountTokenizer()
    assert tokenizer("") == 0
    
    text = "Hello, world! This is a test."
    # Matches: ["Hello", ",", "world", "!", "This", "is", "a", "test", "."] -> 9 tokens
    assert tokenizer(text) == 9

def test_custom_callable_tokenizer():
    # A simple custom character length tokenizer
    custom_tokenizer = lambda text: len(text)
    
    resolved = resolve_tokenizer(custom_tokenizer)
    assert resolved("hello") == 5

def test_resolve_default_tokenizer():
    resolved = resolve_tokenizer(None)
    assert isinstance(resolved, WordCountTokenizer)

def test_resolve_invalid_tokenizer():
    with pytest.raises(TypeError):
        resolve_tokenizer("not-a-callable")

def test_optional_tiktoken_error_if_missing(monkeypatch):
    # Simulate tiktoken not being installed
    import sys
    monkeypatch.setitem(sys.modules, "tiktoken", None)
    
    with pytest.raises(ImportError) as exc_info:
        TiktokenTokenizer()
    
    assert "tiktoken" in str(exc_info.value)

def test_optional_huggingface_error_if_missing(monkeypatch):
    # Simulate transformers not being installed
    import sys
    monkeypatch.setitem(sys.modules, "transformers", None)
    
    with pytest.raises(ImportError) as exc_info:
        HFTokenizer("gpt2")
        
    assert "transformers" in str(exc_info.value)

def test_tiktoken_tokenizer_real():
    # Only test if tiktoken is actually available (not mocked out)
    tokenizer = TiktokenTokenizer("gpt-4")
    assert tokenizer("hello world") == 2

