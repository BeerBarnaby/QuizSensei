from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from app.schemas.question import QuestionGenerationRequest

class BaseQuestionGenerator(ABC):
    """
    Abstract base class for Question Generators.
    Implementations could be rule-based mocks or LLM-driven engines.
    """

    @abstractmethod
    async def generate(
        self, 
        text: str, 
        analysis: Dict[str, Any], 
        request: QuestionGenerationRequest
    ) -> List[Dict[str, Any]]:
        """
        Generates candidate questions based on the source text and its analysis.

        Args:
            text: The full extracted text of the document.
            analysis: The taxonomy, topic, subtopic, and difficulty JSON dictionary from Phase 3.
            request: The filtering constraints (number_of_questions, difficulty, etc).

        Returns:
            A list of dictionary objects conforming to the QuestionDraft schema.
        """
        pass
