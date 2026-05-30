import pytest
from smartchunker import SmartChunker
from smartchunker.elements import Document, HeadingElement, ParagraphElement, TableElement
from smartchunker.chunkers.fixed_element import FixedElementChunker
from smartchunker.chunkers.heading_aware import HeadingAwareChunker
from smartchunker.tokenizers import WordCountTokenizer

def test_fixed_element_chunker_basic():
    # max_tokens of 10 words
    chunker = FixedElementChunker(max_tokens=10, tokenizer=None)
    
    doc = Document()
    doc.add_element(HeadingElement("Title", level=1))             # markdown: "# Title\n" (2 words)
    doc.add_element(ParagraphElement("This is a short sentence.")) # markdown: "This is a short sentence.\n" (5 words)
    doc.add_element(ParagraphElement("This is another sentence.")) # markdown: "This is another sentence.\n" (5 words)
    
    chunks = chunker.chunk(doc)
    
    # Cumulative:
    # Chunk 1: "# Title\n" + "This is a short sentence.\n" -> 7 words (fits <= 10)
    # Chunk 2: "This is another sentence.\n" -> 5 words
    assert len(chunks) == 2
    assert "Title" in chunks[0].text
    assert "short" in chunks[0].text
    assert "another" in chunks[1].text
    assert chunks[0].heading_path == ["Title"]
    assert chunks[1].heading_path == ["Title"]


def test_fixed_element_chunker_splits_oversized_table():
    # Word count tokenizer
    # A large table should be split by row, repeating headers
    headers = ["Name", "Job"]
    rows = [
        ["Alice", "Engineer"],
        ["Bob", "Manager"],
        ["Charlie", "Designer"],
        ["David", "Researcher"]
    ]
    table = TableElement(rows=rows, headers=headers)
    
    doc = Document([table])
    
    # A single table markdown representation:
    # | Name | Job |
    # | --- | --- |
    # | Alice | Engineer | (and so on)
    #
    # If we set max_tokens very low (e.g. 10 words), the table MUST split
    chunker = FixedElementChunker(max_tokens=10, tokenizer=None)
    chunks = chunker.chunk(doc)
    
    # We expect multiple chunks, each containing a TableElement with headers propagated
    assert len(chunks) > 1
    for chunk in chunks:
        # Check that headers exist in every chunk
        assert "Name" in chunk.text
        assert "Job" in chunk.text
        assert "---" in chunk.text
        # Every chunk should contain at least one row
        assert "Alice" in chunk.text or "Bob" in chunk.text or "Charlie" in chunk.text or "David" in chunk.text


def test_fixed_element_chunker_splits_oversized_paragraph():
    text = "This is sentence one. This is sentence two. This is sentence three. This is sentence four."
    p = ParagraphElement(text)
    doc = Document([p])
    
    # A limit of 5 words means sentences will be separated
    chunker = FixedElementChunker(max_tokens=5, tokenizer=None)
    chunks = chunker.chunk(doc)
    
    assert len(chunks) >= 3
    assert "sentence one" in chunks[0].text
    assert "sentence two" in chunks[1].text


def test_heading_aware_chunker():
    doc = Document()
    doc.add_element(HeadingElement("Intro", level=1))
    doc.add_element(ParagraphElement("Paragraph A."))
    doc.add_element(HeadingElement("Details", level=2))
    doc.add_element(ParagraphElement("Paragraph B."))
    
    # Split on headings
    chunker = HeadingAwareChunker(max_tokens=50, tokenizer=None)
    chunks = chunker.chunk(doc)
    
    # Intro starts chunk 1, Details starts chunk 2
    assert len(chunks) == 2
    assert "Intro" in chunks[0].text
    assert "Details" in chunks[1].text
    assert chunks[0].heading_path == ["Intro"]
    assert chunks[1].heading_path == ["Intro", "Details"]


def test_facade_end_to_end():
    md = """# Section One
Text under section one.

# Section Two
Text under section two.
"""
    sc = SmartChunker(max_tokens=100)
    doc = sc.parse_markdown(md, metadata={"doc_id": "my-doc"})
    
    chunks = sc.chunk(doc, strategy="heading-aware")
    
    assert len(chunks) == 2
    assert chunks[0].chunk_id == "my-doc-hchunk-0"
    assert chunks[0].heading_path == ["Section One"]
    assert chunks[1].chunk_id == "my-doc-hchunk-1"
    assert chunks[1].heading_path == ["Section Two"]
