import re
from typing import Dict, Any

from app.services.analyzers.base import BaseAnalyzer


class RuleBasedAnalyzer(BaseAnalyzer):
    """
    Analyzes document text using regex-based keyword matching to classify
    topics strictly within the Financial Literacy domain.
    """

    # Domain vocabulary
    KEYWORD_MAPPING = {
        "Personal Finance": [
            "budget", "saving", "expense", "income", "emergency fund", "debt", "credit card"
        ],
        "Investment": [
            "stock", "bond", "compound interest", "crypto", "dividend", "portfolio", "roi", "index fund"
        ],
        "Economics": [
            "inflation", "interest rate", "gdp", "supply", "demand", "monetary policy"
        ]
    }

    # Complexity markers for difficulty rating
    COMPLEXITY_MARKERS = [
        "derivative", "amortization", "quantitative", "macroeconomics", "volatility",
        "yield curve", "liquidity", "fiduciary", "arbitrage"
    ]

    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        Runs the heuristic keyword scoring on the text.
        """
        text_lower = text.lower()
        
        # 1. Determine Topic by scoring keyword matches
        topic_scores = {topic: 0 for topic in self.KEYWORD_MAPPING.keys()}
        found_keywords = []

        for topic, keywords in self.KEYWORD_MAPPING.items():
            for kw in keywords:
                # Basic whole-word matching using compiled regex
                matches = len(re.findall(f"\\b{kw}\\b", text_lower))
                if matches > 0:
                    topic_scores[topic] += matches
                    if kw not in found_keywords:
                        found_keywords.append(kw)

        # Find the max scoring topic
        primary_topic = "General Financial Literacy" # fallback
        if any(topic_scores.values()):
            primary_topic = max(topic_scores, key=topic_scores.get) # type: ignore

        # 2. Determine Subtopic based on the highest term within the winning topic
        subtopic = "Overview"
        if primary_topic in self.KEYWORD_MAPPING:
            best_kw = None
            max_kw_count = 0
            for kw in self.KEYWORD_MAPPING[primary_topic]:
                count = len(re.findall(f"\\b{kw}\\b", text_lower))
                if count > max_kw_count:
                    max_kw_count = count
                    best_kw = kw
            if best_kw:
                subtopic = best_kw.title()

        # 3. Determine Difficulty
        # Look for advanced terminology mapping to "hard"
        complexity_hits = sum(1 for hw in self.COMPLEXITY_MARKERS if f"\\b{hw}\\b" in text_lower or hw in text_lower)
        
        # Also factor in document length as a proxy for complexity in this MVP
        text_length = len(text)
        
        if complexity_hits >= 3 or text_length > 15000:
            difficulty = "hard"
        elif complexity_hits >= 1 or text_length > 5000:
            difficulty = "medium"
        else:
            difficulty = "easy"

        # 4. Generate candidate learning objective based on the best keyword
        if subtopic != "Overview":
            objective = f"Understand the fundamental concepts of {subtopic.lower()} in the context of {primary_topic.lower()}."
        else:
            objective = f"Grasp the basic principles of {primary_topic.lower()}."

        # Compile results
        return {
            "topic": primary_topic,
            "subtopic": subtopic,
            "difficulty": difficulty,
            "learning_objective_candidate": objective,
            "keywords_found": found_keywords,
            "rationale": f"Rule-based classification found {len(found_keywords)} relevant terms. Scored highest in '{primary_topic}'. Difficulty ranked '{difficulty}' based on vocabulary and length."
        }
