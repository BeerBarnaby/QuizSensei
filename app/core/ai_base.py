from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, text: str) -> Dict[str, Any]:
        pass

class BaseQuestionGenerator(ABC):
    @abstractmethod
    async def generate(
        self, 
        text: str, 
        analysis: Dict[str, Any], 
        request: Any # Avoid circular dependency with QuestionGenerationRequest
    ) -> List[Dict[str, Any]]:
        pass

class BaseAuditor(ABC):
    @abstractmethod
    async def audit(
        self,
        drafts: List[Dict[str, Any]],
        audience: str,
        difficulty: str,
        source_text: str
    ) -> List[Dict[str, Any]]:
        pass
