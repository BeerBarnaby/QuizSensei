"""
app/services/generators/mock_generator.py

Concrete mock implementation of BaseQuestionGenerator for testing the Phase 4 pipeline.
Outputs a strict JSON array conforming to the Pydantic schema constraints.
"""

import uuid
from typing import List, Dict, Any

from app.services.generators.base import BaseQuestionGenerator


class MockQuestionGenerator(BaseQuestionGenerator):
    """
    Dummy generator that fulfills the schema structure without full LLM orchestration.
    Useful for testing the routing, storage, and UI parsing before spending API tokens.
    """

    async def generate(self, text: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Returns a hardcoded draft question mapped to the source document's analysis.
        """
        
        # Pull topic/difficulty from the actual analysis JSON
        topic = analysis.get("topic", "unclassified")
        subtopic = analysis.get("subtopic", "unknown")
        difficulty = analysis.get("difficulty", "medium")

        # Fake Question 1
        qstr_1 = {
            "question_id": f"q_{uuid.uuid4().hex[:8]}",
            "topic": topic,
            "subtopic": subtopic,
            "difficulty": difficulty,
            "question_type": "multiple_choice",
            "stem": f"Based on the text regarding {subtopic.replace('_', ' ')}, which of the following is true?",
            "choices": [
                {"key": "A", "text": "This is a plausible distractor."},
                {"key": "B", "text": "This is the obviously correct answer."},
                {"key": "C", "text": "This is a common misconception."},
                {"key": "D", "text": "This is entirely unrelated."}
            ],
            "correct_answer": "B",
            "rationale_for_correct_answer": "Choice B is supported directly by the text's definition.",
            "rationale_for_incorrect_choices": "A is plausible but wrong. C targets misconception X. D is out of scope.",
            "misconception_tags": ["Misunderstanding basic terms", "Confusing concepts"],
            "source_evidence": text[:100] + "..." if text else "N/A",
            "why_this_question": "Tests foundational knowledge recommended heavily in the provided taxonomy."
        }
        
        # Fake Question 2 (Differs slightly)
        qstr_2 = {
            "question_id": f"q_{uuid.uuid4().hex[:8]}",
            "topic": topic,
            "subtopic": subtopic,
            "difficulty": "hard" if difficulty == "medium" else "medium",
            "question_type": "multiple_choice",
            "stem": "Consider a scenario involving tradeoffs in this domain. What is the BEST approach?",
            "choices": [
                {"key": "A", "text": "Acting impulsively."},
                {"key": "B", "text": "Ignoring the risks."},
                {"key": "C", "text": "Evaluating opportunity costs before deciding."},
                {"key": "D", "text": "Waiting indefinitely."}
            ],
            "correct_answer": "C",
            "rationale_for_correct_answer": "C demonstrates advanced financial reasoning and tradeoff analysis.",
            "rationale_for_incorrect_choices": "A and B increase hazard. D is inaction.",
            "misconception_tags": ["Failure to weigh options"],
            "source_evidence": text[100:200] + "..." if len(text) > 100 else "N/A",
            "why_this_question": "Forces application of abstract concepts to a practical scenario."
        }

        return [qstr_1, qstr_2]
