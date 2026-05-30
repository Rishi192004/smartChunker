from typing import List, Union, Any
from smartchunker.elements import Document, Element
from smartchunker.normalizer import Normalizer
from smartchunker.parsers.markdown import MarkdownParser
from smartchunker.parsers.html import HTMLParser
from smartchunker.chunkers.base import Chunk
from smartchunker.chunkers.fixed_element import FixedElementChunker
from smartchunker.chunkers.heading_aware import HeadingAwareChunker

class SmartChunker:
    """
    Unified facade class for parsing and chunking documents.
    """

    def __init__(
        self,
        max_tokens: int = 512,
        tokenizer: Any = None,
        overlap_tokens: int = 0
    ):
        self.max_tokens = max_tokens
        self.tokenizer = tokenizer
        self.overlap_tokens = overlap_tokens
        self.normalizer = Normalizer()
        self.markdown_parser = MarkdownParser()
        self.html_parser = HTMLParser()

    def parse_markdown(self, text: str, metadata: dict = None) -> Document:
        """Parse markdown string into a standardized Document AST."""
        nodes = self.markdown_parser.parse(text)
        return self.normalizer.normalize(nodes, doc_metadata=metadata)

    def parse_html(self, text: str, metadata: dict = None) -> Document:
        """Parse HTML string into a standardized Document AST."""
        nodes = self.html_parser.parse(text)
        return self.normalizer.normalize(nodes, doc_metadata=metadata)

    def chunk(self, doc: Document, strategy: str = "fixed") -> List[Chunk]:
        """Chunk a parsed Document using the specified strategy ('fixed' or 'heading-aware')."""
        if strategy == "heading-aware":
            chunker = HeadingAwareChunker(
                max_tokens=self.max_tokens,
                tokenizer=self.tokenizer,
                overlap_tokens=self.overlap_tokens
            )
        else:
            chunker = FixedElementChunker(
                max_tokens=self.max_tokens,
                tokenizer=self.tokenizer,
                overlap_tokens=self.overlap_tokens
            )
        return chunker.chunk(doc)

__all__ = [
    "SmartChunker",
    "Document",
    "Element",
    "Chunk"
]
