from typing import List, Dict, Any, Type, TypeVar, Optional
from smartchunker.elements.base import Element

T = TypeVar('T', bound=Element)

class Document:
    """A container representing the structured element tree of a document."""

    def __init__(self, elements: Optional[List[Element]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.elements = elements if elements is not None else []
        self.metadata = metadata if metadata is not None else {}

    def add_element(self, element: Element) -> None:
        """Append an element to the document structure."""
        self.elements.append(element)

    def find_all(self, element_class: Type[T]) -> List[T]:
        """Find and return all elements of a specific type (e.g., TableElement)."""
        return [el for el in self.elements if isinstance(el, element_class)]

    def to_markdown(self) -> str:
        """Combine all elements back into a single Markdown document."""
        return "\n".join(el.to_markdown() for el in self.elements)

    def to_html(self) -> str:
        """Combine all elements back into a single HTML page."""
        return "\n".join(el.to_html() for el in self.elements)

    def __repr__(self) -> str:
        return f"Document(elements_count={len(self.elements)}, metadata={self.metadata})"
