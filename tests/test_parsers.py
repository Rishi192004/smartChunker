import pytest
from smartchunker.parsers.markdown import MarkdownParser
from smartchunker.parsers.html import HTMLParser
from smartchunker.normalizer import Normalizer
from smartchunker.elements import (
    HeadingElement,
    ParagraphElement,
    TableElement,
    CodeBlockElement,
    ListElement
)

def test_markdown_parser():
    md_content = """# Main Title
This is a paragraph with some **bold** text.

## Section 1
Here is a list:
- Item 1
- Item 2

And a code block:
```python
def hello():
    return "world"
```

| Header A | Header B |
| --- | --- |
| Val A1 | Val B1 |
| Val A2 | Val B2 |
"""
    parser = MarkdownParser()
    nodes = parser.parse(md_content)
    
    assert len(nodes) == 8
    assert nodes[0]["type"] == "heading"
    assert nodes[0]["level"] == 1
    assert nodes[0]["text"] == "Main Title"
    
    assert nodes[1]["type"] == "paragraph"
    assert "paragraph with some" in nodes[1]["text"]
    
    assert nodes[2]["type"] == "heading"
    assert nodes[2]["level"] == 2
    
    assert nodes[3]["type"] == "paragraph"
    assert "Here is a list:" in nodes[3]["text"]

    assert nodes[4]["type"] == "list"
    assert nodes[4]["items"] == ["Item 1", "Item 2"]
    assert nodes[4]["ordered"] is False
    
    assert nodes[5]["type"] == "paragraph"
    assert "And a code block:" in nodes[5]["text"]

    assert nodes[6]["type"] == "code"
    assert nodes[6]["language"] == "python"
    assert "def hello()" in nodes[6]["text"]
    
    assert nodes[7]["type"] == "table"
    assert nodes[7]["headers"] == ["Header A", "Header B"]
    assert nodes[7]["rows"] == [["Val A1", "Val B1"], ["Val A2", "Val B2"]]


def test_html_parser():
    html_content = """
    <html>
    <body>
        <h1>Welcome to SmartChunker</h1>
        <p>This is a paragraph of <i>HTML</i> text.</p>
        <div>
            <h2>Section HTML</h2>
            <ol>
                <li>First ordered</li>
                <li>Second ordered</li>
            </ol>
        </div>
        <pre><code class="language-js">console.log("hello");</code></pre>
        <table>
            <thead>
                <tr><th>Column X</th><th>Column Y</th></tr>
            </thead>
            <tbody>
                <tr><td>Val X1</td><td>Val Y1</td></tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    parser = HTMLParser()
    nodes = parser.parse(html_content)
    
    assert len(nodes) == 6
    assert nodes[0]["type"] == "heading"
    assert nodes[0]["level"] == 1
    assert nodes[0]["text"] == "Welcome to SmartChunker"
    
    assert nodes[1]["type"] == "paragraph"
    assert "HTML text" in nodes[1]["text"]
    
    assert nodes[2]["type"] == "heading"
    assert nodes[2]["level"] == 2
    
    assert nodes[3]["type"] == "list"
    assert nodes[3]["items"] == ["First ordered", "Second ordered"]
    assert nodes[3]["ordered"] is True
    
    assert nodes[4]["type"] == "code"
    assert nodes[4]["language"] == "js"
    assert 'console.log("hello");' in nodes[4]["text"]
    
    assert nodes[5]["type"] == "table"
    assert nodes[5]["headers"] == ["Column X", "Column Y"]
    assert nodes[5]["rows"] == [["Val X1", "Val Y1"]]


def test_end_to_end_parsing_and_normalization():
    md_content = """# Integration Test
A simple paragraph.
"""
    parser = MarkdownParser()
    normalizer = Normalizer()
    
    nodes = parser.parse(md_content)
    doc = normalizer.normalize(nodes)
    
    assert len(doc.elements) == 2
    assert isinstance(doc.elements[0], HeadingElement)
    assert isinstance(doc.elements[1], ParagraphElement)
    assert doc.elements[0].text == "Integration Test"
    assert doc.elements[1].text == "A simple paragraph."
