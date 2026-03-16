"""
Base interface for document analyzers.
Defines the required protocol for content classification and sufficiency evaluation.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAnalyzer(ABC):
    """
    Abstract base class for document analyzers.
    Implementations could be rule-based, ML-based, or LLM-based.
    """

    @abstractmethod
    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyzes the extracted text and returns a classification result.

        Args:
            text: The full extracted text of the document.

        Returns:
            A dictionary containing the analysis results (e.g., topic, subtopic, difficulty).
        """
        pass
