from typing import List
from smartchunker.elements import Document, HeadingElement, Element
from smartchunker.chunkers.base import BaseChunker, Chunk
from smartchunker.chunkers.fixed_element import FixedElementChunker

class HeadingAwareChunker(BaseChunker):
    """
    Splits documents along heading boundaries. A heading element always starts a new chunk.
    If a section between headings exceeds max_tokens, it is split sequentially using FixedElementChunker.
    """

    def __init__(
        self,
        max_tokens: int = 512,
        tokenizer = None,
        overlap_tokens: int = 0,
        min_heading_level: int = 6  # Default is to split on any heading (H1 to H6)
    ):
        super().__init__(max_tokens, tokenizer, overlap_tokens)
        self.min_heading_level = min_heading_level
        self._fallback_chunker = FixedElementChunker(max_tokens, tokenizer, overlap_tokens)

    def chunk(self, doc: Document) -> List[Chunk]:
        if not doc.elements:
            return []

        # Pre-calculate heading paths on the full document structure first
        from smartchunker.metadata import propagate_heading_paths
        propagate_heading_paths(doc)

        # Divide elements into heading-delimited sections
        sections: List[List[Element]] = []
        current_section: List[Element] = []

        for el in doc.elements:
            # Check if this element is a heading that triggers a section break
            is_trigger_heading = (
                isinstance(el, HeadingElement) and el.level <= self.min_heading_level
            )
            
            if is_trigger_heading:
                if current_section:
                    sections.append(current_section)
                current_section = [el]
            else:
                current_section.append(el)

        if current_section:
            sections.append(current_section)

        # Chunk each section independently using the fixed-element rules
        chunks: List[Chunk] = []
        chunk_index = 0
        
        # Propagate document-level metadata to sub-documents
        doc_metadata = doc.metadata.copy()

        for idx, section in enumerate(sections):
            # Create a temporary sub-document for this section
            sub_doc = Document(elements=section, metadata=doc_metadata)
            
            # Use FixedElementChunker to chunk this section safely
            section_chunks = self._fallback_chunker.chunk(sub_doc)
            
            # Align IDs and append
            for sc in section_chunks:
                sc.chunk_id = f"{doc_metadata.get('doc_id', 'doc')}-hchunk-{chunk_index}"
                sc.metadata["chunk_id"] = sc.chunk_id
                chunks.append(sc)
                chunk_index += 1

        return chunks
