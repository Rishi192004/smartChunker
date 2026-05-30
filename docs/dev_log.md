# SmartChunker Development Log

This document records the progress, design challenges, and solutions encountered during the development of SmartChunker.

---

## Log Entry: 2026-05-30 — Project Kickoff & Milestone 1

### What was built
1. **Strategic Plan & Task List**: Defined comparison matrices, roadmaps, and structural priorities.
2. **Project Setup**: Configured `pyproject.toml` with poetry, specifying core dependencies (`markdown-it-py`, `beautifulsoup4`) and optional extras (`tiktoken`, `transformers`).

### Design Decisions
* **Normalizer Insertion**: Resolved to put a dedicated `Normalizer` between raw parsers (HTML/Markdown/etc.) and the `Document` AST. Parsers generate raw intermediate nodes (like heading level, raw string, table lists), and the Normalizer formats them into standard `Element` schemas. This makes adding custom parsers extremely easy since they don't need to implement their own element sanitization.
* **Core Tokenizer Interface**: Kept the core library dependency-free by using a standard word-count fallback. Optional adapters wrap `tiktoken` and HuggingFace's tokenizers if the packages are installed.

---

## Log Entry: 2026-05-30 — Milestone 2: Markdown & HTML Parsers + Normalizer

### What was built
1. **BaseParser Interface**: Abstract class mapping all parsers to a common output signature (list of intermediate dictionaries).
2. **MarkdownParser**: Implemented tokenizer token-stream traversal utilizing `markdown-it-py`. Added support for table, lists, fenced code blocks, headings, and paragraphs.
3. **HTMLParser**: Implemented BeautifulSoup tree parsing to classify structural elements.
4. **Normalizer End-to-End**: Standardized raw parser dictionaries into AST nodes, linking parsers to the core element tree.

### Design Decisions & Challenges
* **Markdown-it Linkify dependency**: Initially used `gfm-like` configuration for `markdown-it-py` to get table support. However, it threw a `ModuleNotFoundError` because linkify-it is not installed by default and requires external python libraries. We solved this by using the standard default `MarkdownIt()` configurations and explicitly calling `.enable("table")`. This preserves a clean dependency footprint.
* **Double Processing Prevention**: Markdown-it emits paragraph/inline tokens inside list items and tables. We resolved this by advancing the parser's index pointer `idx` past list item and table scopes during state collection, naturally skipping nested child tags in the primary loops.

---

