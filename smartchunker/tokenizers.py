import re
from typing import Callable, Union, Any

# Protocol signature for tokenizer: Callable[[str], int]
TokenizerType = Callable[[str], int]

class WordCountTokenizer:
    """
    Default fallback tokenizer that counts words using regular expressions.
    Requires zero external dependencies.
    """
    def __init__(self):
        # Match words/numbers or non-whitespace sequences
        self.word_pattern = re.compile(r'\w+|[^\w\s]+')

    def __call__(self, text: str) -> int:
        if not text:
            return 0
        return len(self.word_pattern.findall(text))


class TiktokenTokenizer:
    """
    Tokenizer adapter utilizing the OpenAI tiktoken library.
    Requires `pip install smartchunker[tiktoken]`.
    """
    def __init__(self, model_name: str = "gpt-4"):
        try:
            import tiktoken
        except ImportError:
            raise ImportError(
                "The 'tiktoken' library is required to use TiktokenTokenizer. "
                "Please install it using: pip install smartchunker[tiktoken]"
            )
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except Exception:
            # Fallback to general cl100k_base encoding if model lookup fails
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def __call__(self, text: str) -> int:
        if not text:
            return 0
        return len(self.encoding.encode(text))


class HFTokenizer:
    """
    Tokenizer adapter utilizing the HuggingFace transformers library.
    Requires `pip install smartchunker[huggingface]`.
    """
    def __init__(self, model_name: str, **kwargs: Any):
        try:
            from transformers import AutoTokenizer
        except ImportError:
            raise ImportError(
                "The 'transformers' library is required to use HFTokenizer. "
                "Please install it using: pip install smartchunker[huggingface]"
            )
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, **kwargs)

    def __call__(self, text: str) -> int:
        if not text:
            return 0
        return len(self.tokenizer.encode(text))


def resolve_tokenizer(tokenizer: Union[TokenizerType, None]) -> TokenizerType:
    """Resolves tokenizer argument into a Callable[[str], int]."""
    if tokenizer is None:
        return WordCountTokenizer()
    if callable(tokenizer):
        return tokenizer
    raise TypeError(
        f"Tokenizer must be a Callable[[str], int] or None, got {type(tokenizer)}"
    )
