import sys
import types
import pytest
from smartchunker.chunkers.base import Chunk
from smartchunker.adapters import LangChainAdapter, LlamaIndexAdapter

def test_langchain_adapter_missing(monkeypatch):
    # Simulate missing langchain-core
    monkeypatch.setitem(sys.modules, "langchain_core.documents", None)
    chunk = Chunk("test text", {"key": "val"}, [], 5, "id-0", ["H1"])
    
    with pytest.raises(ImportError) as exc_info:
        LangChainAdapter.to_document(chunk)
        
    assert "langchain-core" in str(exc_info.value)


def test_langchain_adapter_success(monkeypatch):
    # Mock langchain_core.documents.Document
    class MockDocument:
        def __init__(self, page_content: str, metadata: dict):
            self.page_content = page_content
            self.metadata = metadata

    mock_mod = types.ModuleType("langchain_core.documents")
    mock_mod.Document = MockDocument
    monkeypatch.setitem(sys.modules, "langchain_core.documents", mock_mod)
    
    chunk = Chunk("hello world", {"source": "web"}, [], 2, "id-1", ["Intro"])
    doc = LangChainAdapter.to_document(chunk)
    
    assert doc.page_content == "hello world"
    assert doc.metadata["source"] == "web"


def test_llamaindex_adapter_missing(monkeypatch):
    # Simulate missing llama-index-core
    monkeypatch.setitem(sys.modules, "llama_index.core.schema", None)
    chunk = Chunk("test text", {"key": "val"}, [], 5, "id-0", ["H1"])
    
    with pytest.raises(ImportError) as exc_info:
        LlamaIndexAdapter.to_node(chunk)
        
    assert "llama-index-core" in str(exc_info.value)


def test_llamaindex_adapter_success(monkeypatch):
    # Mock llama_index.core.schema.TextNode
    class MockTextNode:
        def __init__(self, text: str, id_: str, metadata: dict):
            self.text = text
            self.id_ = id_
            self.metadata = metadata

    mock_mod = types.ModuleType("llama_index.core.schema")
    mock_mod.TextNode = MockTextNode
    monkeypatch.setitem(sys.modules, "llama_index.core.schema", mock_mod)
    
    chunk = Chunk("hello world", {"source": "web"}, [], 2, "id-2", ["Intro"])
    node = LlamaIndexAdapter.to_node(chunk)
    
    assert node.text == "hello world"
    assert node.id_ == "id-2"
    assert node.metadata["source"] == "web"
