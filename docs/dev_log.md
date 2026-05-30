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
