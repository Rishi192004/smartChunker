from typing import List, Dict, Any, Optional
from markdown_it import MarkdownIt
from smartchunker.parsers.base import BaseParser

class MarkdownParser(BaseParser):
    """
    Parses Markdown text into intermediate dictionaries using markdown-it-py.
    """

    def parse(self, text: str) -> List[Dict[str, Any]]:
        # Initialize markdown-it and enable table parsing rules
        md = MarkdownIt().enable("table")
        try:
            tokens = md.parse(text)
        except Exception:
            # Fallback for parsing errors
            return [{"type": "paragraph", "text": text}]

        elements: List[Dict[str, Any]] = []
        
        idx = 0
        n = len(tokens)
        
        while idx < n:
            token = tokens[idx]
            
            # --- HEADINGS ---
            if token.type == "heading_open":
                level = int(token.tag[1]) if (token.tag and len(token.tag) > 1) else 1
                heading_text = ""
                # Find the corresponding inline content
                while idx + 1 < n and tokens[idx + 1].type != "heading_close":
                    idx += 1
                    if tokens[idx].type == "inline":
                        heading_text += tokens[idx].content
                elements.append({
                    "type": "heading",
                    "text": heading_text.strip(),
                    "level": level
                })
            
            # --- PARAGRAPHS ---
            elif token.type == "paragraph_open":
                # Ensure we are not inside a list item or table to avoid double parsing
                # markdown-it wraps list item texts in paragraphs sometimes
                is_nested = False
                # We can check parent or surrounding elements if needed, but a simpler
                # way is checking if we are already building a list or table.
                # However, since we process sequentially, we can track list nesting level.
                p_text = ""
                while idx + 1 < n and tokens[idx + 1].type != "paragraph_close":
                    idx += 1
                    if tokens[idx].type == "inline":
                        p_text += tokens[idx].content
                
                # Check if this paragraph is inside a list item
                # markdown-it represents lists with block structures. We will handle
                # lists and tables explicitly. If we see paragraph_open outside lists, we capture it.
                # Let's skip appending to elements if we are actively inside list parsing.
                # To do this cleanly, we can look at the token's nesting / parent structure.
                # But a cleaner recursive/stack-based state parser is best.
                # Let's write a simple state checker:
                elements.append({
                    "type": "paragraph",
                    "text": p_text.strip()
                })

            # --- CODE FENCES / BLOCKS ---
            elif token.type in ("fence", "code_block"):
                language = token.info.strip() if token.info else ""
                elements.append({
                    "type": "code",
                    "text": token.content.strip(),
                    "language": language
                })
            
            # --- LISTS ---
            elif token.type in ("bullet_list_open", "ordered_list_open"):
                ordered = (token.type == "ordered_list_open")
                items = []
                list_depth = 1
                
                # Consume list tokens until the matching list close
                while idx + 1 < n and list_depth > 0:
                    idx += 1
                    curr_token = tokens[idx]
                    
                    if curr_token.type in ("bullet_list_open", "ordered_list_open"):
                        list_depth += 1
                    elif curr_token.type in ("bullet_list_close", "ordered_list_close"):
                        list_depth -= 1
                    elif curr_token.type == "list_item_open":
                        item_text = ""
                        item_depth = 1
                        while idx + 1 < n and item_depth > 0:
                            idx += 1
                            item_token = tokens[idx]
                            if item_token.type == "list_item_open":
                                item_depth += 1
                            elif item_token.type == "list_item_close":
                                item_depth -= 1
                            elif item_token.type == "inline":
                                item_text += item_token.content
                            elif item_token.type in ("bullet_list_open", "ordered_list_open"):
                                # If there is a nested list, we can format it inline or collect it.
                                # For simplicity, we just append a newline and keep parsing
                                item_text += "\n"
                            elif item_token.type == "paragraph_open":
                                # Skip paragraph tags inside lists, just take inline
                                pass
                        items.append(item_text.strip())
                
                elements.append({
                    "type": "list",
                    "items": [it for it in items if it],
                    "ordered": ordered
                })
            
            # --- TABLES ---
            elif token.type == "table_open":
                headers: List[str] = []
                rows: List[List[str]] = []
                
                in_thead = False
                current_row: List[str] = []
                
                while idx + 1 < n and tokens[idx + 1].type != "table_close":
                    idx += 1
                    curr_token = tokens[idx]
                    
                    if curr_token.type == "thead_open":
                        in_thead = True
                    elif curr_token.type == "thead_close":
                        in_thead = False
                    elif curr_token.type == "tr_open":
                        current_row = []
                    elif curr_token.type == "tr_close":
                        if in_thead:
                            headers = current_row
                        else:
                            rows.append(current_row)
                    elif curr_token.type in ("th_open", "td_open"):
                        cell_text = ""
                        # Find matching close tag
                        close_type = "th_close" if curr_token.type == "th_open" else "td_close"
                        while idx + 1 < n and tokens[idx + 1].type != close_type:
                            idx += 1
                            cell_token = tokens[idx]
                            if cell_token.type == "inline":
                                cell_text += cell_token.content
                        current_row.append(cell_text.strip())
                
                elements.append({
                    "type": "table",
                    "headers": headers,
                    "rows": rows
                })

            idx += 1
            
        # Post-process: when list or table items are processed, markdown-it-py still
        # emits paragraph / inline tokens inside them. To prevent double parsing:
        # We can clean up elements. If an element's text is fully contained inside a list item
        # or table cell that occurred around it, we can filter it out, or we can use a more precise
        # tokenizer matching.
        # Let's fix this cleanly. A standard token streams includes:
        # bullet_list_open
        #   list_item_open
        #     paragraph_open
        #       inline (content)
        #     paragraph_close
        #   list_item_close
        # bullet_list_close
        #
        # Because we jumped forward when we saw `bullet_list_open` or `table_open` to consume all sub-tokens,
        # our outer loop `idx` variable is incremented past all the tokens inside the list/table.
        # Thus, the outer loop will NOT visit those paragraph_open / tr_open tokens again!
        # This is a beautiful property of jumping the index `idx`.
        # However, let's verify if paragraph parser does not double count. It doesn't, because we do `idx += 1` inside
        # the paragraph while-loop as well. Let's make sure we do not skip anything unintended.
        
        # One thing: sometimes we have empty paragraphs or stray tags. Let's clean them up.
        cleaned_elements = []
        for el in elements:
            if el["type"] == "paragraph" and not el["text"]:
                continue
            if el["type"] == "list" and not el["items"]:
                continue
            if el["type"] == "table" and not el["rows"] and not el["headers"]:
                continue
            cleaned_elements.append(el)
            
        return cleaned_elements
