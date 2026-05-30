from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from smartchunker.elements import Element, Document
from smartchunker.tokenizers import TokenizerType, resolve_tokenizer

class Chunk:
    """
    Represents a structured document chunk.
    """

    def __init__(
        self,
        text: str,
        metadata: Dict[str, Any],
        source_elements: List[Element],
        token_count: int,
        chunk_id: str,
        heading_path: List[str]
    ):
        self.text = text
        self.metadata = metadata if metadata is not None else {}
        self.source_elements = source_elements
        self.token_count = token_count
        self.chunk_id = chunk_id
        self.heading_path = heading_path
        
        # Propagate fields to metadata for vector stores that only look at metadata dicts
        self.metadata["chunk_id"] = chunk_id
        self.metadata["heading_path"] = heading_path
        self.metadata["token_count"] = token_count

    def __repr__(self) -> str:
        return (
            f"Chunk(id={self.chunk_id}, tokens={self.token_count}, "
            f"heading_path={self.heading_path}, elements={len(self.source_elements)})"
        )


class BaseChunker(ABC):
    """
    Abstract Base Class for all chunking strategies.
    """

    def __init__(
        self,
        max_tokens: int = 512,
        tokenizer: Optional[TokenizerType] = None,
        overlap_tokens: int = 0
    ):
        self.max_tokens = max_tokens
        self.tokenizer = resolve_tokenizer(tokenizer)
        self.overlap_tokens = overlap_tokens

    @abstractmethod
    def chunk(self, doc: Document) -> List[Chunk]:
        """
        Split a parsed Document into a list of Chunk objects.
        """
        pass
