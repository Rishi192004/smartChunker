from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag, NavigableString
from smartchunker.parsers.base import BaseParser

class HTMLParser(BaseParser):
    """
    Parses HTML documents into intermediate element dictionaries using BeautifulSoup.
    """

    def parse(self, text: str) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(text, "html.parser")
        # Start traversal from body if present, otherwise from the root
        root = soup.body if soup.body else soup
        
        elements: List[Dict[str, Any]] = []
        self._traverse(root, elements)
        
        # Clean up empty elements
        cleaned = []
        for el in elements:
            if el["type"] == "paragraph" and not el["text"].strip():
                continue
            if el["type"] == "list" and not el["items"]:
                continue
            if el["type"] == "table" and not el["rows"] and not el["headers"]:
                continue
            cleaned.append(el)
            
        return cleaned

    def _traverse(self, node: Any, elements: List[Dict[str, Any]]) -> None:
        if isinstance(node, NavigableString):
            text = str(node).strip()
            if text:
                elements.append({"type": "paragraph", "text": text})
            return

        if not isinstance(node, Tag):
            return

        tag_name = node.name.lower()

        # --- HEADINGS ---
        if tag_name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag_name[1])
            elements.append({
                "type": "heading",
                "text": node.get_text().strip(),
                "level": level
            })
            return

        # --- TABLES ---
        elif tag_name == "table":
            headers = []
            rows = []
            
            # Find headers
            for th in node.find_all("th"):
                headers.append(th.get_text().strip())
                
            # Find rows (excluding headers if they are inside a tr)
            for tr in node.find_all("tr"):
                cells = [td.get_text().strip() for td in tr.find_all("td")]
                if cells:
                    rows.append(cells)
                    
            # If headers were not found via th, check if the first row has th elements
            if not headers:
                first_tr = node.find("tr")
                if first_tr:
                    headers = [th.get_text().strip() for th in first_tr.find_all("th")]
                    
            elements.append({
                "type": "table",
                "headers": headers if headers else None,
                "rows": rows
            })
            return

        # --- LISTS ---
        elif tag_name in ("ul", "ol"):
            ordered = (tag_name == "ol")
            items = []
            for li in node.find_all("li", recursive=False):
                # Clean child tags inside li if necessary, but taking text is usually robust
                items.append(li.get_text().strip())
            elements.append({
                "type": "list",
                "items": items,
                "ordered": ordered
            })
            return

        # --- CODE BLOCKS ---
        elif tag_name in ("pre", "code"):
            # Check if this is pre containing code
            code_tag = node.find("code") if tag_name == "pre" else node
            
            # Extract language from class if present (e.g. class="language-python")
            language = ""
            if code_tag and code_tag.has_attr("class"):
                for cls in code_tag["class"]:
                    if cls.startswith("language-"):
                        language = cls.split("-")[1]
                        break
                        
            text_content = code_tag.get_text() if code_tag else node.get_text()
            elements.append({
                "type": "code",
                "text": text_content.strip(),
                "language": language
            })
            return

        # --- PARAGRAPHS ---
        elif tag_name == "p":
            elements.append({
                "type": "paragraph",
                "text": node.get_text().strip()
            })
            return

        # --- CONTAINER BLOCKS (div, section, article, etc.) ---
        # If it's a container tag, we check if it has block-level children.
        # If it does, we traverse them. If it only contains text/inline elements, we treat it as a paragraph.
        block_tags = {"h1", "h2", "h3", "h4", "h5", "h6", "table", "ul", "ol", "pre", "code", "p", "div", "section", "article"}
        has_block_child = False
        for child in node.children:
            if isinstance(child, Tag) and child.name.lower() in block_tags:
                has_block_child = True
                break
                
        if has_block_child:
            for child in node.children:
                self._traverse(child, elements)
        else:
            text = node.get_text().strip()
            if text:
                elements.append({
                    "type": "paragraph",
                    "text": text
                })
