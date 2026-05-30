from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseParser(ABC):
    """Abstract Base Class for parsers that extract structure into raw element dictionaries."""

    @abstractmethod
    def parse(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse raw input string and return a list of intermediate element dictionaries.
        Each dictionary should match the schema expected by the Normalizer.
        """
        pass
