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

## Log Entry: 2026-05-30 — Milestone 3: Tokenizer Interface & Adapters

### What was built
1. **WordCountTokenizer**: Reusable regex-based word/punctuation counter requiring zero external packages. Used as the default fallback.
2. **TiktokenTokenizer Adapter**: Custom wrapper for OpenAI's `tiktoken` that dynamically loads cl100k_base if model lookup fails.
3. **HFTokenizer Adapter**: Custom wrapper for HuggingFace `transformers` tokenizer clients.
4. **resolve_tokenizer helper**: Resolves input arg (None, Callable, or specific wrapper instance) into standard Callable format for chunking strategies.

### Design Decisions & Challenges
* **Mock testing optional extras**: We needed to verify that the library throws correct custom `ImportError` exceptions when libraries are missing, even if the testing environment actually has them installed. We solved this by using `monkeypatch` to force `sys.modules["tiktoken"] = None` and `sys.modules["transformers"] = None` in tests, checking that the user-friendly errors are triggered correctly.
* **Tested Live Tiktoken**: Installed `tiktoken` in our test runner environment and added real testing assertions to ensure token count matches exactly (e.g., "hello world" counts as 2 tokens).

---

## Log Entry: 2026-05-30 — Milestones 4 & 5: Chunk Engine, Strategies, and Metadata Engine

### What was built
1. **Chunk Model**: Represents the output containing `text`, `metadata`, `source_elements`, `token_count`, `chunk_id`, and `heading_path`.
2. **FixedElementChunker**: Implements sequential element grouping. Checks whether individual elements (paragraphs, lists, code blocks, tables) exceed `max_tokens` and splits them structure-safely using specific sub-splitters.
3. **HeadingAwareChunker**: Automatically splits documents on heading levels (H1 to H6), using the heading boundary as the start of a new chunk, falling back to fixed element chunking inside large sections.
4. **Metadata Engines**:
   - `propagate_heading_paths`: Traverses document to build a state-based parent heading path breadcrumb list.
   - `split_table_element`: Re-packages a large table row-by-row into smaller table instances, repeating column headers in each sub-table.

### Design Decisions & Challenges
* **Heading Path Context Loss in Section Chunking**: In `HeadingAwareChunker`, elements are divided into isolated sub-documents (sections) before chunking. However, this caused `propagate_heading_paths` inside the sub-documents to lose context of higher-level headings from previous sections. We resolved this by pre-propagating heading paths across the *entire* document first, and configuring `FixedElementChunker` to skip path propagation if elements already carry heading paths.
* **Granular Element Splitting**: If a paragraph or code block is larger than `max_tokens`, simply packing it as-is violates strict token budgets. We built safe fallback segment splits (sentence token boundaries for text, line bounds for code blocks, individual items for lists, and row bounds for tables) to guarantee strict bounds.

---



