# SmartChunker 🌲

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org/project/smartchunker/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)

**SmartChunker** is to document splitting what **BeautifulSoup** is to HTML parsing: simple, composable, framework-agnostic, and structural.

Most RAG pipelines fail because standard recursive splitters blindly slice tables, code blocks, and list items in half, destroying their semantic coherence. SmartChunker parses Markdown or HTML documents into an **Element Abstract Syntax Tree (AST)**, then splits them safely along structural boundaries—automatically propagating parent heading paths and repeating table headers on broken sub-chunks.

## ⚡ The 60-Second Install & 5-Minute Proof

Can you see why SmartChunker is useful in under 5 minutes? **Yes.**

1. **Install in under 10 seconds** (zero heavy system compilation binaries):
   ```bash
   pip install smartchunker
   ```
2. **Verify in 2 seconds** by running our built-in comparative benchmark demo:
   ```bash
   smartchunker-demo
   ```
This prints a side-by-side diagnostic showing how standard character splitters slice tables in half, while SmartChunker keeps layouts intact, repeats headers, and injects parent heading paths as breadcrumbs.

---

## ✨ Features

- 🌲 **Zero Framework Lock-in**: Output chunks as plain objects, or export directly to **LangChain** and **LlamaIndex**.
- 📊 **Table-Preserving Splits**: Splitting an oversized table dynamically packages it row-by-row and repeats the headers on every sub-chunk.
- 🔗 **Parent Header Breadcrumbs**: Paragraph and code blocks carry their hierarchical heading context (e.g. `["Manual", "Setup", "Config"]`) directly in their metadata.
- 📦 **Zero-Dependency by Default**: Runs on pure Python standard library regex. Optionally install adapters for OpenAI's `tiktoken` or HuggingFace `transformers`.
- 💻 **Syntax-Aware Code Slices**: Keeps code fences intact and tags their language syntax.

---

## 🚀 Quickstart

### 1. Installation

```bash
# Core package (zero dependencies)
pip install smartchunker

# With Tiktoken support (OpenAI models)
pip install smartchunker[tiktoken]

# With HuggingFace support
pip install smartchunker[huggingface]
```

### 2. Basic Ingest & Split

```python
from smartchunker import SmartChunker
from smartchunker.tokenizers import TiktokenTokenizer

# Initialize facade client
chunker = SmartChunker(
    max_tokens=256,
    tokenizer=TiktokenTokenizer("gpt-4")
)

# Parse Markdown or HTML into a Document AST
doc = chunker.parse_markdown("""
# Introduction
SmartChunker parses documents into tree elements.

## Features
- Preserves tables.
- Preserves code.
""")

# Chunk document (options: 'fixed' or 'heading-aware')
chunks = chunker.chunk(doc, strategy="heading-aware")

for chunk in chunks:
    print(f"--- Chunk (ID: {chunk.chunk_id}) ---")
    print(f"Breadcrumb: {chunk.heading_path}")
    print(f"Content:\n{chunk.text}\n")
```

---

## 🛠️ Custom Tokenizers

SmartChunker is future-proof. You can pass a standard Python `Callable[[str], int]` directly to the facade:

```python
# Use character length
chunker = SmartChunker(
    max_tokens=500,
    tokenizer=lambda text: len(text)
)

# Or a custom model encoder
def my_custom_tokenizer(text: str) -> int:
    return len(my_custom_model.encode(text))

chunker = SmartChunker(
    max_tokens=500,
    tokenizer=my_custom_tokenizer
)
```

## 🔌 Unstructured.io Direct Integration & Supported Formats

Depending on whether you use **Unstructured.io** or run SmartChunker standalone, the range of supported document formats changes:

| Ingestion Setup | Supported File Formats | How it works |
| :--- | :--- | :--- |
| **Standalone (No Unstructured)** | **Markdown** (`.md`) and **HTML** (`.html`) | Uses built-in standard library regex, `markdown-it-py`, and `BeautifulSoup` to parse paragraphs, tables, lists, and code blocks. |
| **With Unstructured.io** | **PDFs, Word Docs (`.docx`), PowerPoint (`.pptx`), Images, Emails (`.eml`), Excel (`.xlsx`), and more** | Unstructured.io handles raw file ingestion and extracts layout structures, while SmartChunker normalizes and chunks the resulting outputs. |

SmartChunker natively translates JSON dictionary output elements from the **Unstructured.io** partitioning engine, enabling you to run structure-aware chunking over parsed PDFs, DOCXs, and slides with zero custom translation logic:

*   **Titles and Headers** map directly to `HeadingElement` nodes.
*   **ListItems** map directly to list nodes.
*   **Tables** automatically parse cell arrays and rows from Unstructured's `metadata.text_as_html` property to guarantee boundary-safe splits.

```python
from smartchunker import SmartChunker
from smartchunker.normalizer import Normalizer

# Raw output array from Unstructured client / API partition
unstructured_payload = [
    {"type": "Title", "text": "API Manual"},
    {"type": "Table", "text": "Fallback text", "metadata": {"text_as_html": "<table>...</table>"}}
]

# Normalize and chunk instantly
doc = Normalizer().normalize(unstructured_payload)
chunks = SmartChunker(max_tokens=256).chunk(doc)
```

> [!NOTE]
> *Active development is underway to expand SmartChunker's native format parsers (such as direct PDF reading) and other performance improvements.*

---

## 🔌 Framework Export Adapters

Integrate seamlessly into your existing workflows:

### Export to LangChain
```python
from smartchunker.adapters import LangChainAdapter

# Convert SmartChunker chunks to langchain_core.documents.Document
lc_docs = LangChainAdapter.to_documents(chunks)
```

### Export to LlamaIndex
```python
from smartchunker.adapters import LlamaIndexAdapter

# Convert SmartChunker chunks to llama_index.core.schema.TextNode
li_nodes = LlamaIndexAdapter.to_nodes(chunks)
```

---

## 🤝 Contributing

We welcome contributions to make document ingestion clean and painless!

1. Clone the repository: `git clone https://github.com/Rishi192004/smartChunker.git`
2. Set up virtual environment and install packages: `python -m venv .venv`
3. Run tests using Pytest: `python -m pytest tests/`

Please read our contributing guidelines for details on our code formatting and AST normalizer schemas.
