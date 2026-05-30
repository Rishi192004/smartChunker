import uuid
from typing import List, Dict, Any
from smartchunker.elements import Document, Element, HeadingElement, TableElement
from smartchunker.tokenizers import TokenizerType

def propagate_heading_paths(doc: Document) -> None:
    """
    Traverse a Document and update each element's metadata with its heading path.
    Example heading path: ["SmartChunker Manual", "Installation", "Pip Setup"]
    """
    # Track current active headings by level (1-indexed, level 1 to 6)
    current_path: List[str] = []
    current_levels: List[int] = []

    for el in doc.elements:
        if isinstance(el, HeadingElement):
            level = el.level
            
            # Trim the path to remove heading elements of the same or deeper levels
            while current_levels and current_levels[-1] >= level:
                current_levels.pop()
                current_path.pop()
                
            current_levels.append(level)
            current_path.append(el.text)
            
            # Headings also carry their own path (excluding themselves in parent path if desired,
            # but usually carrying their full path is good)
            el.metadata["heading_path"] = list(current_path)
        else:
            el.metadata["heading_path"] = list(current_path)


def split_table_element(
    table: TableElement,
    max_tokens: int,
    tokenizer: TokenizerType
) -> List[TableElement]:
    """
    Splits a large TableElement into smaller TableElement chunks,
    propagating the table headers to each sub-table chunk.
    """
    # If the entire table fits in the budget, return it as-is
    entire_text = table.to_markdown()
    if tokenizer(entire_text) <= max_tokens or not table.rows:
        return [table]

    sub_tables: List[TableElement] = []
    current_rows: List[List[str]] = []
    
    # Calculate base tokens for headers and table boundary overhead
    headers_text = ""
    if table.headers:
        headers_text = "| " + " | ".join(table.headers) + " |\n| " + " | ".join(["---"] * len(table.headers)) + " |\n"
    
    base_overhead = tokenizer(headers_text)

    for row in table.rows:
        row_text = "| " + " | ".join(row) + " |\n"
        row_tokens = tokenizer(row_text)
        
        # Estimate combined size of headers + accumulated rows + current row
        temp_rows = current_rows + [row]
        temp_table = TableElement(rows=temp_rows, headers=table.headers)
        temp_tokens = tokenizer(temp_table.to_markdown())
        
        if temp_tokens <= max_tokens:
            current_rows.append(row)
        else:
            # If current_rows is empty, it means even a single row + header exceeds max_tokens.
            # We must add it to avoid losing data, then start a new one.
            if not current_rows:
                current_rows.append(row)
                sub_tables.append(TableElement(rows=current_rows, headers=table.headers, metadata=table.metadata.copy()))
                current_rows = []
            else:
                # Flush the current sub-table
                sub_tables.append(TableElement(rows=current_rows, headers=table.headers, metadata=table.metadata.copy()))
                # Start new sub-table with this row
                current_rows = [row]

    if current_rows:
        sub_tables.append(TableElement(rows=current_rows, headers=table.headers, metadata=table.metadata.copy()))

    return sub_tables
