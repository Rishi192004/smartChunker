import pytest
from smartchunker.elements import (
    Document,
    HeadingElement,
    ParagraphElement,
    TableElement,
    CodeBlockElement,
    ListElement
)
from smartchunker.normalizer import Normalizer

def test_heading_element():
    heading = HeadingElement("Introduction", level=2)
    assert heading.level == 2
    assert heading.to_markdown() == "## Introduction\n"
    assert heading.to_html() == "<h2>Introduction</h2>\n"

def test_paragraph_element():
    p = ParagraphElement("Hello world.")
    assert p.to_markdown() == "Hello world.\n"
    assert p.to_html() == "<p>Hello world.</p>\n"

def test_table_element():
    headers = ["Name", "Age"]
    rows = [["Alice", "30"], ["Bob", "25"]]
    table = TableElement(rows=rows, headers=headers)
    assert "Name | Age" in table.text
    assert "| Name | Age |" in table.to_markdown()
    assert "<table>" in table.to_html()
    assert "<th>Name</th>" in table.to_html()
    assert "<td>Alice</td>" in table.to_html()

def test_code_block_element():
    code = CodeBlockElement("print('hello')", language="python")
    assert code.to_markdown() == "```python\nprint('hello')\n```\n"
    assert "class=\"language-python\"" in code.to_html()

def test_list_element():
    items = ["Apple", "Banana"]
    unordered = ListElement(items, ordered=False)
    ordered = ListElement(items, ordered=True)
    assert "- Apple" in unordered.to_markdown()
    assert "1. Apple" in ordered.to_markdown()
    assert "<ul>" in unordered.to_html()
    assert "<ol>" in ordered.to_html()

def test_document():
    doc = Document()
    doc.add_element(HeadingElement("Title", 1))
    doc.add_element(ParagraphElement("Para"))
    
    headings = doc.find_all(HeadingElement)
    assert len(headings) == 1
    assert headings[0].text == "Title"
    assert "# Title" in doc.to_markdown()

def test_normalizer():
    raw_nodes = [
        {"type": "heading", "text": "Header 1", "level": 1},
        {"type": "paragraph", "text": "This is a body text."},
        {
            "type": "table",
            "headers": ["ColA", "ColB"],
            "rows": [["1", "2"]]
        },
        {"type": "code", "text": "x = 10", "language": "python"},
        {"type": "list", "items": ["Item A", "Item B"], "ordered": True}
    ]
    
    normalizer = Normalizer()
    doc = normalizer.normalize(raw_nodes)
    
    assert len(doc.elements) == 5
    assert isinstance(doc.elements[0], HeadingElement)
    assert isinstance(doc.elements[1], ParagraphElement)
    assert isinstance(doc.elements[2], TableElement)
    assert isinstance(doc.elements[3], CodeBlockElement)
    assert isinstance(doc.elements[4], ListElement)
    
    assert doc.elements[0].level == 1
    assert doc.elements[2].headers == ["ColA", "ColB"]
    assert doc.elements[3].language == "python"
    assert doc.elements[4].ordered is True
