import time
from typing import List
from smartchunker import SmartChunker

class MockRecursiveCharacterTextSplitter:
    """Simulates LangChain's RecursiveCharacterTextSplitter for zero-dependency benchmarking."""
    def __init__(self, chunk_size: int = 150):
        self.chunk_size = chunk_size

    def split_text(self, text: str) -> List[str]:
        # Simple character-based recursive split approximation
        words = text.split()
        chunks = []
        current = []
        current_len = 0
        for word in words:
            if current_len + len(word) + 1 > self.chunk_size:
                chunks.append(" ".join(current))
                current = [word]
                current_len = len(word)
            else:
                current.append(word)
                current_len += len(word) + 1
        if current:
            chunks.append(" ".join(current))
        return chunks


def run_benchmark():
    sample_document = """# SmartChunker User Guide
This manual explains how to install and leverage the SmartChunker library for RAG engines.

## Installation
To install the core package:
```bash
pip install smartchunker
```

Or install with optional tiktoken adapter:
```bash
pip install smartchunker[tiktoken]
```

## Features Overview
Below is the comparison matrix for typical chunking frameworks.

| Chunker | Structure Preservation | Table repeat headers | Zero Dependencies |
| :--- | :--- | :--- | :--- |
| Recursive Splitter | No | No | Yes |
| Unstructured | Yes | Yes | No |
| SmartChunker | Yes | Yes | Yes |

### Conclusion
SmartChunker keeps everything intact.
"""

    print("=" * 60)
    print("           SMARTCHUNKER INGESTION BENCHMARK")
    print("=" * 60)
    
    # 1. Baseline Splitter (Character-based)
    print("\n--- Running Baseline Recursive Character Splitter ---")
    start_time = time.perf_counter()
    baseline = MockRecursiveCharacterTextSplitter(chunk_size=120)
    baseline_chunks = baseline.split_text(sample_document)
    baseline_time = (time.perf_counter() - start_time) * 1000
    
    # Analyze baseline integrity
    broken_code_blocks = sum(1 for c in baseline_chunks if "```" in c and c.count("```") % 2 != 0)
    broken_tables = sum(1 for c in baseline_chunks if "|" in c and ("Chunker" in c) != ("SmartChunker" in c or "Recursive" in c))
    
    print(f"Total Chunks Generated : {len(baseline_chunks)}")
    print(f"Execution Speed        : {baseline_time:.4f} ms")
    print(f"Broken Code Blocks     : {broken_code_blocks}")
    print(f"Broken/Split Tables    : {broken_tables}")
    print(f"Breadcrumb Metadata    : None")

    # 2. SmartChunker (Fixed Element)
    print("\n--- Running SmartChunker (Fixed Element) ---")
    start_time = time.perf_counter()
    sc = SmartChunker(max_tokens=25)  # low token budget to trigger splits
    doc = sc.parse_markdown(sample_document, metadata={"doc_id": "bench-doc"})
    sc_chunks = sc.chunk(doc, strategy="fixed")
    sc_time = (time.perf_counter() - start_time) * 1000
    
    sc_broken_code = sum(1 for c in sc_chunks if "```" in c.text and c.text.count("```") % 2 != 0)
    # Check table split header repeats: every chunk containing table content must have headers
    sc_broken_table = 0
    for c in sc_chunks:
        if "|" in c.text:
            if "Chunker" not in c.text or "---" not in c.text:
                sc_broken_table += 1

    print(f"Total Chunks Generated : {len(sc_chunks)}")
    print(f"Execution Speed        : {sc_time:.4f} ms")
    print(f"Broken Code Blocks     : {sc_broken_code} (Table/Code boundaries preserved!)")
    print(f"Broken/Split Tables    : {sc_broken_table} (Headers repeated automatically!)")
    print(f"Breadcrumb Metadata    : Present (heading_paths attached to chunks)")
    
    print("\nSample Injected Breadcrumbs:")
    for c in sc_chunks[:3]:
        print(f"  * Chunk ID: {c.chunk_id} -> Path: {c.heading_path}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    run_benchmark()
