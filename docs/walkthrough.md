# SmartChunker V1 Technical Walkthrough

This document summarizes the directory structure, design implementation, test suite results, and ingestion benchmark metrics of **SmartChunker** V1.

---

## 🌲 Repository Structure

The codebase is organized as follows:

```
smartchunker/
├── smartchunker/
│   ├── __init__.py             # Facade interface
│   ├── elements/               # AST Element definitions
│   │   ├── base.py             # Abstract Element class
│   │   ├── types.py            # Heading, Table, Paragraph, CodeBlock, List
│   │   └── document.py         # Document AST container
│   ├── parsers/                # Parsers returning dict streams
│   │   ├── base.py             # Abstract parser
│   │   ├── markdown.py         # markdown-it-py parser
│   │   └── html.py             # BeautifulSoup parser
│   ├── normalizer.py           # Standardizes raw dicts to AST elements
│   ├── tokenizers.py           # Tokenizer interfaces, Tiktoken/HF adapters
│   ├── chunkers/               # Splitting strategies
│   │   ├── base.py             # Abstract chunker and Chunk model
│   │   ├── fixed_element.py    # Group elements safely by token budget
│   │   └── heading_aware.py    # Split on heading boundaries
│   ├── metadata.py             # Heading path & Table splitting utilities
│   ├── adapters/               # Deferred integrations
│   │   ├── langchain.py        # LangChain core adapter
│   │   └── llamaindex.py       # LlamaIndex core adapter
│   └── evaluation/
│       └── benchmark.py        # Structural integrity benchmarking
├── tests/                      # Pytest suite
│   ├── test_elements.py
│   ├── test_parsers.py
│   ├── test_tokenizers.py
│   ├── test_chunkers.py
│   └── test_adapters.py
├── docs/
│   ├── dev_log.md              # Detailed developmental progression log
│   └── walkthrough.md          # Technical walkthrough (this file)
├── pyproject.toml              # Build & optional extras configuration
└── .gitignore
```

---

## ⚡ Verification Results

### 1. Pytest Coverage
The test suite consists of **26 test cases** verifying all components, including parsers, AST normalizer mappings, custom tokenizer fallbacks, live tiktoken tokenizer outputs, mock ecosystem mappings, element splitting boundaries, and nested header propagation.

```powershell
.venv\Scripts\python.exe -m pytest tests/
```

**Output**:
```
============================= test session starts =============================
platform win32 -- Python 3.14.2, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\Lenovo\Desktop\smartChunker
configfile: pyproject.toml
collected 26 items

tests\test_adapters.py ....                                              [ 15%]
tests\test_chunkers.py .....                                             [ 34%]
tests\test_elements.py .......                                           [ 61%]
tests\test_parsers.py ...                                                [ 73%]
tests\test_tokenizers.py .......                                         [100%]

============================= 26 passed in 0.82s ==============================
```

---

### 2. Live Ingestion Benchmarking
The evaluation benchmark compares SmartChunker's structure-aware splitting against a recursive character splitter baseline on a markdown document containing nested headings, a code block, and a markdown table.

```powershell
.venv\Scripts\python.exe -m smartchunker.evaluation.benchmark
```

**Results**:
```
============================================================
           SMARTCHUNKER INGESTION BENCHMARK
============================================================

--- Running Baseline Recursive Character Splitter ---
Total Chunks Generated : 6
Execution Speed        : 0.0455 ms
Broken Code Blocks     : 0
Broken/Split Tables    : 1   <-- Table split in half; labels separated from values!
Breadcrumb Metadata    : None

--- Running SmartChunker (Fixed Element) ---
Total Chunks Generated : 7
Execution Speed        : 2.0968 ms
Broken Code Blocks     : 0 (Table/Code boundaries preserved!)
Broken/Split Tables    : 0 (Headers repeated automatically!) <-- PERFECT!
Breadcrumb Metadata    : Present (heading_paths attached to chunks)

Sample Injected Breadcrumbs:
  * Chunk ID: bench-doc-chunk-0 -> Path: ['SmartChunker User Guide']
  * Chunk ID: bench-doc-chunk-1 -> Path: ['SmartChunker User Guide', 'Installation']
  * Chunk ID: bench-doc-chunk-2 -> Path: ['SmartChunker User Guide', 'Installation']

============================================================
```

#### Key Ingestion Insight:
Standard splitters cut tables and lists at arbitrary characters, confusing embeddings.
SmartChunker **automatically splits tables row-by-row** when they exceed token bounds and **prepends headers to each sub-table**, guaranteeing that tabular structures remain semantically parseable by language models.

---

## 🛠️ Module Design Highlights

### A. Facade Interface
The top-level `SmartChunker` client maps raw text inputs to chunks in three lines:
```python
from smartchunker import SmartChunker

sc = SmartChunker(max_tokens=256)
doc = sc.parse_markdown(markdown_text)
chunks = sc.chunk(doc, strategy="heading-aware")
```

### B. Flexible Tokenizers
SmartChunker runs zero-dependency out-of-the-box using a word/punctuation counter regex, but supports:
```python
from smartchunker.tokenizers import TiktokenTokenizer, HFTokenizer

# Tiktoken (OpenAI)
chunker = SmartChunker(tokenizer=TiktokenTokenizer("gpt-4"))

# HuggingFace Transformers
chunker = SmartChunker(tokenizer=HFTokenizer("meta-llama/Llama-3-8B"))

# Custom Callbacks
chunker = SmartChunker(tokenizer=lambda text: len(text.split()))
```

### C. Unified Chunk Format
Output chunks preserve complete context:
```python
# Fields on Chunk objects:
chunk.chunk_id          # Unique ID string e.g., 'doc-chunk-0'
chunk.text              # Standardized Markdown chunk text
chunk.metadata          # Meta fields (including heading_path, chunk_id, etc.)
chunk.source_elements   # Original concrete AST Elements
chunk.token_count       # Accurate token count
chunk.heading_path      # Heading breadcrumbs path array e.g., ['Installation', 'Pip Setup']
```
