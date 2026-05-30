from typing import List, Dict, Any, Optional
from smartchunker.elements.base import Element

class HeadingElement(Element):
    """Represents a heading element (H1 to H6)."""

    def __init__(self, text: str, level: int, metadata: Dict[str, Any] = None):
        super().__init__(text, metadata)
        self.level = level
        self.metadata["level"] = level

    def to_markdown(self) -> str:
        return f"{'#' * self.level} {self.text}\n"

    def to_html(self) -> str:
        return f"<h{self.level}>{self.text}</h{self.level}>\n"


class ParagraphElement(Element):
    """Represents standard narrative paragraph text."""

    def to_markdown(self) -> str:
        return f"{self.text}\n"

    def to_html(self) -> str:
        return f"<p>{self.text}</p>\n"


class TableElement(Element):
    """Represents a table structure containing headers and rows."""

    def __init__(
        self,
        rows: List[List[str]],
        headers: Optional[List[str]] = None,
        metadata: Dict[str, Any] = None
    ):
        self.headers = headers if headers is not None else []
        self.rows = rows
        
        # Construct raw text representation for fallback searches
        text_lines = []
        if self.headers:
            text_lines.append(" | ".join(self.headers))
        for row in self.rows:
            text_lines.append(" | ".join(row))
        full_text = "\n".join(text_lines)
        
        super().__init__(full_text, metadata)
        self.metadata["type"] = "table"

    def to_markdown(self) -> str:
        lines = []
        if self.headers:
            lines.append("| " + " | ".join(self.headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(self.headers)) + " |")
        elif self.rows:
            # Fallback border if no headers are provided
            col_count = len(self.rows[0])
            lines.append("| " + " | ".join([""] * col_count) + " |")
            lines.append("| " + " | ".join(["---"] * col_count) + " |")
            
        for row in self.rows:
            lines.append("| " + " | ".join(row) + " |")
            
        return "\n".join(lines) + "\n"

    def to_html(self) -> str:
        html = ["<table>"]
        if self.headers:
            html.append("  <thead>")
            html.append("    <tr>")
            for header in self.headers:
                html.append(f"      <th>{header}</th>")
            html.append("    </tr>")
            html.append("  </thead>")
            
        html.append("  <tbody>")
        for row in self.rows:
            html.append("    <tr>")
            for cell in row:
                html.append(f"      <td>{cell}</td>")
            html.append("    </tr>")
        html.append("  </tbody>")
        html.append("</table>\n")
        return "\n".join(html)


class CodeBlockElement(Element):
    """Represents code blocks with syntax highlighting language markers."""

    def __init__(
        self,
        text: str,
        language: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ):
        super().__init__(text, metadata)
        self.language = language or ""
        self.metadata["language"] = self.language

    def to_markdown(self) -> str:
        lang = self.language
        return f"```{lang}\n{self.text}\n```\n"

    def to_html(self) -> str:
        lang_class = f' class="language-{self.language}"' if self.language else ""
        return f"<pre><code{lang_class}>{self.text}</code></pre>\n"


class ListElement(Element):
    """Represents a list of items, which can be ordered or unordered."""

    def __init__(
        self,
        items: List[str],
        ordered: bool = False,
        metadata: Dict[str, Any] = None
    ):
        self.items = items
        self.ordered = ordered
        
        # Text representation is space-delimited or line-delimited items
        prefix = "1. " if ordered else "- "
        full_text = "\n".join(f"{prefix}{item}" for item in self.items)
        
        super().__init__(full_text, metadata)
        self.metadata["ordered"] = ordered

    def to_markdown(self) -> str:
        lines = []
        for idx, item in enumerate(self.items):
            prefix = f"{idx + 1}. " if self.ordered else "- "
            lines.append(f"{prefix}{item}")
        return "\n".join(lines) + "\n"

    def to_html(self) -> str:
        tag = "ol" if self.ordered else "ul"
        html = [f"<{tag}>"]
        for item in self.items:
            html.append(f"  <li>{item}</li>")
        html.append(f"</{tag}>\n")
        return "\n".join(html)
