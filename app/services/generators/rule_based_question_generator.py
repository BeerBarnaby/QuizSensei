"""
app/services/generators/rule_based_question_generator.py

Rule-Based Question Generator that loads from a static question bank JSON.
No LLM calls – instant, deterministic, and cost-free.
"""

import json
import random
import uuid
from pathlib import Path
from typing import List, Dict, Any

from app.core.config import Settings
from app.services.generators.base import BaseQuestionGenerator
from app.schemas.question import QuestionGenerationRequest


class RuleBasedQuestionGenerator(BaseQuestionGenerator):
    """
    Loads questions from a static JSON question bank and filters
    by topic, subtopic, difficulty, and count.
    """

    BANK_PATH = Path(__file__).parent.parent.parent / "data" / "question_bank.json"

    def __init__(self, settings: Settings):
        self.settings = settings
        self._bank: List[Dict[str, Any]] = self._load_bank()

    def _load_bank(self) -> List[Dict[str, Any]]:
        """Load the question bank JSON from disk once at startup."""
        if not self.BANK_PATH.exists():
            raise FileNotFoundError(f"Question bank not found at: {self.BANK_PATH}")
        with open(self.BANK_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    async def generate(
        self,
        text: str,
        analysis: Dict[str, Any],
        request: QuestionGenerationRequest,
    ) -> List[Dict[str, Any]]:
        """
        Filters the question bank based on request parameters.
        Falls back gracefully if filters yield no results.
        """
        pool = list(self._bank)  # Work on a copy

        # ── Apply optional filters ─────────────────────────────────────────
        topic = request.topic_filter or analysis.get("topic")
        subtopic = request.subtopic_filter or analysis.get("subtopic")
        difficulty = request.difficulty_filter or analysis.get("difficulty")

        if topic:
            filtered = [q for q in pool if q.get("topic") == topic]
            if filtered:
                pool = filtered

        if subtopic:
            filtered = [q for q in pool if q.get("subtopic") == subtopic]
            if filtered:
                pool = filtered

        if difficulty:
            filtered = [q for q in pool if q.get("difficulty", "").lower() == difficulty.lower()]
            if filtered:
                pool = filtered

        # ── Random sample up to requested count ───────────────────────────
        n = min(request.number_of_questions, len(pool))
        selected = random.sample(pool, n) if n > 0 else []

        # ── Inject a fresh question_id for each selected question ──────────
        results = []
        for q in selected:
            item = q.copy()
            item["question_id"] = f"q_{uuid.uuid4().hex[:8]}"
            results.append(item)

        return results
