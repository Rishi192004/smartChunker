import sys
import types
import pytest
from smartchunker import SmartChunker
from smartchunker.elements import (
    Document,
    HeadingElement,
    ParagraphElement,
    TableElement,
    CodeBlockElement,
    ListElement
)
from smartchunker.normalizer import Normalizer
from smartchunker.tokenizers import TiktokenTokenizer, HFTokenizer
from smartchunker.chunkers.base import Chunk
from smartchunker.chunkers.fixed_element import FixedElementChunker
from smartchunker.chunkers.heading_aware import HeadingAwareChunker
from smartchunker.adapters import LangChainAdapter, LlamaIndexAdapter
from smartchunker.parsers.html import HTMLParser
from smartchunker.parsers.markdown import MarkdownParser
from smartchunker.metadata import split_table_element

def test_normalizer_fallback():
    # Test unrecognized type fallback to ParagraphElement
    raw_node = {"type": "weird_custom_type", "text": "hello fallback"}
    el = Normalizer.normalize_element(raw_node)
    assert isinstance(el, ParagraphElement)
    assert el.text == "hello fallback"


def test_element_reprs():
    heading = HeadingElement("A", level=2)
    assert "HeadingElement(text='A'..., metadata=" in repr(heading)
    
    doc = Document([heading])
    assert "Document(elements_count=1, metadata=" in repr(doc)
    
    chunk = Chunk("text", {}, [heading], 10, "chunk-1", ["Intro"])
    assert "Chunk(id=chunk-1, tokens=10, heading_path=['Intro'], elements=1)" in repr(chunk)


def test_document_to_html():
    doc = Document([ParagraphElement("Hello HTML")])
    html = doc.to_html()
    assert "<p>Hello HTML</p>" in html


def test_facade_missing_branches():
    # Test html parsing through facade
    sc = SmartChunker(max_tokens=100)
    doc = sc.parse_html("<h1>Welcome</h1>")
    assert len(doc.elements) == 1
    assert doc.elements[0].text == "Welcome"
    
    # Test facade chunk with strategy="fixed"
    chunks = sc.chunk(doc, strategy="fixed")
    assert len(chunks) == 1


def test_adapters_list_exporters(monkeypatch):
    # Mock langchain
    class MockDocument:
        def __init__(self, page_content: str, metadata: dict):
            self.page_content = page_content
            self.metadata = metadata

    mock_langchain = types.ModuleType("langchain_core.documents")
    mock_langchain.Document = MockDocument
    monkeypatch.setitem(sys.modules, "langchain_core.documents", mock_langchain)
    
    # Mock llamaindex
    class MockTextNode:
        def __init__(self, text: str, id_: str, metadata: dict):
            self.text = text
            self.id_ = id_
            self.metadata = metadata

    mock_llama = types.ModuleType("llama_index.core.schema")
    mock_llama.TextNode = MockTextNode
    monkeypatch.setitem(sys.modules, "llama_index.core.schema", mock_llama)

    chunk = Chunk("content", {}, [], 5, "id-0", [])
    
    lc_docs = LangChainAdapter.to_documents([chunk])
    assert len(lc_docs) == 1
    assert lc_docs[0].page_content == "content"
    
    li_nodes = LlamaIndexAdapter.to_nodes([chunk])
    assert len(li_nodes) == 1
    assert li_nodes[0].text == "content"


def test_empty_chunkers_input():
    doc = Document()
    assert FixedElementChunker().chunk(doc) == []
    assert HeadingAwareChunker().chunk(doc) == []


def test_table_element_without_headers():
    table = TableElement(rows=[["A", "B"]], headers=None)
    md = table.to_markdown()
    assert "| A | B |" in md
    assert "| --- | --- |" in md


def test_metadata_table_splitter_edge_cases():
    # Empty table rows splits
    table = TableElement(rows=[], headers=["ColA"])
    splits = split_table_element(table, 10, lambda t: len(t.split()))
    assert len(splits) == 1
    assert splits[0] == table

    # Table splits where single row exceeds max token budget
    table = TableElement(
        rows=[
            ["ThisIsAVeryLongValueThatWillDefinitelyExceedTenWordsOnItsOwn"],
            ["Short"]
        ],
        headers=["Header"]
    )
    # Budget of 2 words (forces splitting immediately)
    splits = split_table_element(table, 2, lambda t: len(t.split()))
    assert len(splits) == 2
    assert splits[0].rows == [["ThisIsAVeryLongValueThatWillDefinitelyExceedTenWordsOnItsOwn"]]
    assert splits[1].rows == [["Short"]]


def test_tokenizer_edge_cases(monkeypatch):
    # Test tiktoken model fallback
    # Pass non-existent model to trigger Exception catch inside TiktokenTokenizer
    tokenizer = TiktokenTokenizer("non-existent-gpt-model")
    assert tokenizer("hello world") == 2
    
    # Test empty string returns 0 tokens
    assert tokenizer("") == 0

    # Test HFTokenizer successful instantiation and calls using mock
    class MockAutoTokenizer:
        @classmethod
        def from_pretrained(cls, name, **kwargs):
            return cls()
        def encode(self, text):
            return [1, 2, 3] if text else []

    mock_trans = types.ModuleType("transformers")
    mock_trans.AutoTokenizer = MockAutoTokenizer
    monkeypatch.setitem(sys.modules, "transformers", mock_trans)
    
    hf_tok = HFTokenizer("mock-model")
    assert hf_tok("hello") == 3
    assert hf_tok("") == 0


def test_html_parser_edge_cases():
    parser = HTMLParser()
    
    # Clean up empty elements branch
    nodes = parser.parse("<p></p><ul></ul><table></table>")
    assert len(nodes) == 0

    # NavigableString at root level
    nodes = parser.parse("Raw text without tags")
    assert len(nodes) == 1
    assert nodes[0]["type"] == "paragraph"
    assert nodes[0]["text"] == "Raw text without tags"

    # Non-tag node traversal return
    # BS4 comment is a non-tag child
    nodes = parser.parse("<!-- This is a comment -->")
    assert len(nodes) == 0

    # Table tr with th fallback check
    nodes = parser.parse("<table><tr><th>Col1</th></tr><tr><td>Val1</td></tr></table>")
    assert len(nodes) == 1
    assert nodes[0]["type"] == "table"
    assert nodes[0]["headers"] == ["Col1"]
    assert nodes[0]["rows"] == [["Val1"]]

    # Container tag with no block children (treats text as paragraph)
    nodes = parser.parse("<div>Only some inline <span>text</span></div>")
    assert len(nodes) == 1
    assert nodes[0]["type"] == "paragraph"
    assert nodes[0]["text"] == "Only some inline text"


def test_markdown_parser_edge_cases(monkeypatch):
    parser = MarkdownParser()
    
    # Check that empty string parses to zero elements
    nodes = parser.parse("")
    assert len(nodes) == 0

    # Parse exception fallback
    class MockMarkdownIt:
        def __init__(self, *args, **kwargs):
            pass
        def enable(self, *args):
            return self
        def parse(self, text):
            raise Exception("Parsing error simulation")

    monkeypatch.setattr("smartchunker.parsers.markdown.MarkdownIt", MockMarkdownIt)
    nodes = parser.parse("# Header Text")
    assert len(nodes) == 1
    assert nodes[0]["type"] == "paragraph"
    assert nodes[0]["text"] == "# Header Text"


def test_markdown_parser_nested_lists():
    # Test nested lists parsing where children are collected inline under parent item
    parser = MarkdownParser()
    md = """- Parent Item
  - Child Item A
  - Child Item B
"""
    nodes = parser.parse(md)
    assert len(nodes) == 1
    assert nodes[0]["type"] == "list"
    assert len(nodes[0]["items"]) == 1
    assert "Parent Item" in nodes[0]["items"][0]
    assert "Child Item A" in nodes[0]["items"][0]
    assert "Child Item B" in nodes[0]["items"][0]


def test_fixed_element_chunker_oversized_elements():
    # Test splitting giant CodeBlock and List elements
    # Using 10 words budget
    chunker = FixedElementChunker(max_tokens=10, tokenizer=None)
    
    # Giant CodeBlock (more than 10 words line length)
    giant_code = "line1 word word word word word\nline2 word word word word word"
    doc_code = Document([CodeBlockElement(giant_code, "python")])
    chunks_code = chunker.chunk(doc_code)
    assert len(chunks_code) >= 2
    assert "line1" in chunks_code[0].text
    assert "line2" in chunks_code[1].text

    # Giant List (each list item counts as words, list items will split)
    giant_list = ListElement(["item1 word word word word", "item2 word word word word"], ordered=False)
    doc_list = Document([giant_list])
    chunks_list = chunker.chunk(doc_list)
    assert len(chunks_list) >= 2
    assert "item1" in chunks_list[0].text
    assert "item2" in chunks_list[1].text


def test_unstructured_normalizer_mappings():
    raw_nodes = [
        {"type": "Title", "text": "Unstructured Title"},
        {"type": "Header", "text": "Unstructured H2"},
        {"type": "NarrativeText", "text": "Unstructured Paragraph"},
        {"type": "ListItem", "text": "Bullet Item"},
        {
            "type": "Table",
            "text": "Fallback text",
            "metadata": {
                "text_as_html": "<table><thead><tr><th>H1</th></tr></thead><tbody><tr><td>V1</td></tr></tbody></table>"
            }
        }
    ]
    
    normalizer = Normalizer()
    doc = normalizer.normalize(raw_nodes)
    
    assert len(doc.elements) == 5
    
    assert isinstance(doc.elements[0], HeadingElement)
    assert doc.elements[0].level == 1
    assert doc.elements[0].text == "Unstructured Title"
    
    assert isinstance(doc.elements[1], HeadingElement)
    assert doc.elements[1].level == 2
    
    assert isinstance(doc.elements[2], ParagraphElement)
    assert doc.elements[2].text == "Unstructured Paragraph"
    
    assert isinstance(doc.elements[3], ListElement)
    assert doc.elements[3].items == ["Bullet Item"]
    
    assert isinstance(doc.elements[4], TableElement)
    assert doc.elements[4].headers == ["H1"]
    assert doc.elements[4].rows == [["V1"]]

