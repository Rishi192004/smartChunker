from typing import List, Any
from smartchunker.chunkers.base import Chunk

class LangChainAdapter:
    """
    Adapter to export SmartChunker Chunk objects to LangChain Documents.
    """

    @staticmethod
    def to_document(chunk: Chunk) -> Any:
        """Convert a single SmartChunker Chunk into a langchain_core Document."""
        try:
            from langchain_core.documents import Document as LCDoc
        except ImportError:
            raise ImportError(
                "The 'langchain-core' package is required to export to LangChain. "
                "Please install it using: pip install langchain-core"
            )
        return LCDoc(page_content=chunk.text, metadata=chunk.metadata.copy())

    @classmethod
    def to_documents(cls, chunks: List[Chunk]) -> List[Any]:
        """Convert a list of SmartChunker Chunks into a list of langchain_core Documents."""
        return [cls.to_document(c) for c in chunks]
