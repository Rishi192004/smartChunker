from typing import List, Dict, Any, Optional
from smartchunker.elements import (
    Document,
    Element,
    HeadingElement,
    ParagraphElement,
    TableElement,
    CodeBlockElement,
    ListElement
)

class Normalizer:
    """
    Standardizes intermediate parser representations (dictionaries)
    into concrete SmartChunker Element classes, generating a clean Document AST.
    """

    @staticmethod
    def normalize_element(raw_node: Dict[str, Any]) -> Element:
        """
        Convert a raw dictionary node representation into a concrete Element instance.
        
        Expected raw_node structure:
        {
            "type": "heading" | "paragraph" | "table" | "code" | "list",
            "text": str,                      # (or rows/items as appropriate)
            "level": int,                     # Required for heading
            "headers": List[str],             # Optional for table
            "rows": List[List[str]],          # Required for table
            "language": str,                  # Optional for code
            "items": List[str],               # Required for list
            "ordered": bool,                  # Optional for list
            "metadata": Dict[str, Any]        # Optional
        }
        """
        node_type = raw_node.get("type", "").lower()
        metadata = raw_node.get("metadata", {})
        
        # --- Core Format Mappings & Unstructured Mappings ---
        if node_type == "heading":
            level = int(raw_node.get("level", 1))
            text = raw_node.get("text", "")
            return HeadingElement(text=text, level=level, metadata=metadata)
            
        elif node_type == "title":
            # Map Unstructured Title to H1 Heading
            text = raw_node.get("text", "")
            return HeadingElement(text=text, level=1, metadata=metadata)
            
        elif node_type == "header":
            # Map Unstructured Header to H2 Heading
            text = raw_node.get("text", "")
            return HeadingElement(text=text, level=2, metadata=metadata)
            
        elif node_type in ("paragraph", "narrativetext", "text", "uncategorizedtext"):
            text = raw_node.get("text", "")
            return ParagraphElement(text=text, metadata=metadata)
            
        elif node_type == "table":
            # Check if this is an Unstructured table containing HTML in metadata
            html_table = metadata.get("text_as_html", "")
            if html_table:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_table, "html.parser")
                    headers = [th.get_text().strip() for th in soup.find_all("th")]
                    rows = []
                    for tr in soup.find_all("tr"):
                        cells = [td.get_text().strip() for td in tr.find_all("td")]
                        if cells:
                            rows.append(cells)
                    if rows:
                        return TableElement(rows=rows, headers=headers if headers else None, metadata=metadata)
                except Exception:
                    pass
            
            # Default Core Table parsing
            rows = raw_node.get("rows", [])
            headers = raw_node.get("headers", None)
            return TableElement(rows=rows, headers=headers, metadata=metadata)
            
        elif node_type == "code":
            text = raw_node.get("text", "")
            language = raw_node.get("language", "")
            return CodeBlockElement(text=text, language=language, metadata=metadata)
            
        elif node_type == "list":
            items = raw_node.get("items", [])
            ordered = bool(raw_node.get("ordered", False))
            return ListElement(items=items, ordered=ordered, metadata=metadata)
            
        elif node_type == "listitem":
            # Map Unstructured ListItem
            text = raw_node.get("text", "")
            return ListElement(items=[text], ordered=False, metadata=metadata)
            
        else:
            # Fallback to general paragraph if type is unrecognized
            text = raw_node.get("text", str(raw_node))
            return ParagraphElement(text=text, metadata=metadata)

    def normalize(self, raw_nodes: List[Dict[str, Any]], doc_metadata: Optional[Dict[str, Any]] = None) -> Document:
        """Convert a list of raw nodes into a unified Document AST."""
        elements = [self.normalize_element(node) for node in raw_nodes if node]
        return Document(elements=elements, metadata=doc_metadata)
