import uuid
import re
from typing import List, Dict, Any, cast
from smartchunker.elements import (
    Element,
    Document,
    ParagraphElement,
    TableElement,
    CodeBlockElement,
    ListElement
)
from smartchunker.chunkers.base import BaseChunker, Chunk
from smartchunker.metadata import propagate_heading_paths, split_table_element

class FixedElementChunker(BaseChunker):
    """
    Groups elements sequentially. Ensures that boundaries never cross structural boundaries
    unless a single element exceeds max_tokens, in which case the element is split structure-safely.
    """

    def chunk(self, doc: Document) -> List[Chunk]:
        if not doc.elements:
            return []

        # Step 1: Propagate heading paths to element metadata if not already present
        # This preserves full paths when HeadingAwareChunker splits document into sections
        if any("heading_path" not in el.metadata for el in doc.elements):
            propagate_heading_paths(doc)

        # Step 2: Split elements that exceed max_tokens internally
        processed_elements: List[Element] = []
        for el in doc.elements:
            processed_elements.extend(self._split_element_if_needed(el))

        # Step 3: Group elements into chunks
        chunks: List[Chunk] = []
        current_group: List[Element] = []
        current_tokens = 0
        
        # Unique document prefix for chunk IDs
        doc_id = doc.metadata.get("doc_id", str(uuid.uuid4())[:8])
        chunk_index = 0

        for el in processed_elements:
            el_text = el.to_markdown()
            el_tokens = self.tokenizer(el_text)
            
            # If current group has items and adding this element exceeds max_tokens, flush
            if current_group and (current_tokens + el_tokens > self.max_tokens):
                chunks.append(self._create_chunk(current_group, doc_id, chunk_index, current_tokens))
                chunk_index += 1
                current_group = [el]
                current_tokens = el_tokens
            else:
                current_group.append(el)
                current_tokens += el_tokens

        if current_group:
            chunks.append(self._create_chunk(current_group, doc_id, chunk_index, current_tokens))

        return chunks

    def _create_chunk(self, elements: List[Element], doc_id: str, index: int, token_count: int) -> Chunk:
        # Concatenate markdown representation
        text = "".join(el.to_markdown() for el in elements).strip()
        
        # Take the heading path from the first element that has one, default to empty list
        heading_path = []
        for el in elements:
            if "heading_path" in el.metadata:
                heading_path = el.metadata["heading_path"]
                break
                
        # Consolidate metadata
        metadata = {}
        # Merge metadata from elements, prioritizing source document metadata if passed
        for el in elements:
            # Propagate any custom fields
            for k, v in el.metadata.items():
                if k not in ("heading_path", "level", "language", "ordered"):
                    metadata[k] = v
                    
        chunk_id = f"{doc_id}-chunk-{index}"
        return Chunk(
            text=text,
            metadata=metadata,
            source_elements=elements,
            token_count=token_count,
            chunk_id=chunk_id,
            heading_path=heading_path
        )

    def _split_element_if_needed(self, el: Element) -> List[Element]:
        el_text = el.to_markdown()
        if self.tokenizer(el_text) <= self.max_tokens:
            return [el]

        # Element exceeds max_tokens, perform structure-specific splitting
        if isinstance(el, TableElement):
            # split_table_element returns List[TableElement]; cast to List[Element]
            return cast(List[Element], split_table_element(el, self.max_tokens, self.tokenizer))
            
        elif isinstance(el, ParagraphElement):
            # Split paragraph into sentences using basic punctuation regex
            sentences = re.split(r'(?<=[.!?])\s+', el.text)
            sub_paragraphs: List[Element] = []
            curr_text = []
            
            for sentence in sentences:
                temp_text = " ".join(curr_text + [sentence])
                if self.tokenizer(temp_text) <= self.max_tokens:
                    curr_text.append(sentence)
                else:
                    if curr_text:
                        sub_paragraphs.append(ParagraphElement(" ".join(curr_text), el.metadata.copy()))
                        curr_text = [sentence]
                    else:
                        # Single sentence is too long, append anyway
                        sub_paragraphs.append(ParagraphElement(sentence, el.metadata.copy()))
                        curr_text = []
            if curr_text:
                sub_paragraphs.append(ParagraphElement(" ".join(curr_text), el.metadata.copy()))
            return sub_paragraphs

        elif isinstance(el, CodeBlockElement):
            # Split code block by lines
            lines = el.text.split("\n")
            sub_codes: List[Element] = []
            curr_lines = []
            
            for line in lines:
                temp_text = "\n".join(curr_lines + [line])
                # Count with markdown fences wrapped around to check true tokens
                temp_element = CodeBlockElement(temp_text, el.language)
                if self.tokenizer(temp_element.to_markdown()) <= self.max_tokens:
                    curr_lines.append(line)
                else:
                    if curr_lines:
                        sub_codes.append(CodeBlockElement("\n".join(curr_lines), el.language, el.metadata.copy()))
                        curr_lines = [line]
                    else:
                        sub_codes.append(CodeBlockElement(line, el.language, el.metadata.copy()))
                        curr_lines = []
            if curr_lines:
                sub_codes.append(CodeBlockElement("\n".join(curr_lines), el.language, el.metadata.copy()))
            return sub_codes

        elif isinstance(el, ListElement):
            # Split list by list items
            sub_lists: List[Element] = []
            curr_items = []
            
            for item in el.items:
                temp_element = ListElement(curr_items + [item], el.ordered)
                if self.tokenizer(temp_element.to_markdown()) <= self.max_tokens:
                    curr_items.append(item)
                else:
                    if curr_items:
                        sub_lists.append(ListElement(curr_items, el.ordered, el.metadata.copy()))
                        curr_items = [item]
                    else:
                        sub_lists.append(ListElement([item], el.ordered, el.metadata.copy()))
                        curr_items = []
            if curr_items:
                sub_lists.append(ListElement(curr_items, el.ordered, el.metadata.copy()))
            return sub_lists

        else:
            # Fallback for headings or other types - keep intact
            return [el]
