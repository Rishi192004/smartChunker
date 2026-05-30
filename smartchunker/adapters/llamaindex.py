from typing import List, Any
from smartchunker.chunkers.base import Chunk

class LlamaIndexAdapter:
    """
    Adapter to export SmartChunker Chunk objects to LlamaIndex TextNodes.
    """

    @staticmethod
    def to_node(chunk: Chunk) -> Any:
        """Convert a single SmartChunker Chunk into a LlamaIndex TextNode."""
        try:
            from llama_index.core.schema import TextNode
        except ImportError:
            # Fallback check for older/alternate packaging imports if needed,
            # but llama_index.core is the modern standard.
            raise ImportError(
                "The 'llama-index-core' package is required to export to LlamaIndex. "
                "Please install it using: pip install llama-index-core"
            )
        return TextNode(
            text=chunk.text,
            id_=chunk.chunk_id,
            metadata=chunk.metadata.copy()
        )

    @classmethod
    def to_nodes(cls, chunks: List[Chunk]) -> List[Any]:
        """Convert a list of SmartChunker Chunks into a list of LlamaIndex TextNodes."""
        return [cls.to_node(c) for c in chunks]
