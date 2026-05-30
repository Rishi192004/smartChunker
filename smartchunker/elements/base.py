from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class Element(ABC):
    """Abstract Base Class representing a document layout element."""

    def __init__(self, text: str, metadata: Optional[Dict[str, Any]] = None):
        self.text = text
        self.metadata = metadata if metadata is not None else {}

    @abstractmethod
    def to_markdown(self) -> str:
        """Convert the element to its Markdown representation."""
        pass

    @abstractmethod
    def to_html(self) -> str:
        """Convert the element to its HTML representation."""
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(text={repr(self.text[:30])}..., metadata={self.metadata})"
