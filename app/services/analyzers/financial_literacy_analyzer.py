"""
app/services/analyzers/financial_literacy_analyzer.py

Concrete implementation of BaseAnalyzer tailored for the EvalMind Financial Literacy prototype.
Classifies text into specific topics, subtopics, and difficulty levels, and generates
bilingual candidate learning objectives.
"""

import re
from typing import Dict, Any

from app.services.analyzers.base import BaseAnalyzer


class FinancialLiteracyAnalyzer(BaseAnalyzer):
    """
    Heuristic analyzer mapping to the exact 6 Financial Literacy topics:
    1. budgeting_and_spending
    2. saving_and_emergency_fund
    3. credit_and_debt
    4. risk_and_insurance
    5. investment_basics
    6. consumer_rights_and_financial_fraud
    """

    # Primary Taxonomy Mapping
    TAXONOMY = {
        "budgeting_and_spending": {
            "needs_vs_wants": ["need", "want", "essential", "luxury", "desire", "necessity"],
            "fixed_vs_variable_expenses": ["fixed expense", "variable expense", "rent", "utility bill", "groceries", "subscription"],
            "monthly_budgeting": ["budgeting", "monthly planner", "cash flow", "income tracking", "expense tracking", "envelope system"]
        },
        "saving_and_emergency_fund": {
            "savings_goals": ["goal", "target", "milestone", "saving plan", "down payment", "vacation fund", "retirement goal"],
            "emergency_fund": ["emergency", "safety net", "rainy day", "unexpected expense", "medical bill", "loss of income"],
            "delayed_gratification": ["patience", "delay", "waiting", "impulse buy", "discipline", "long-term reward"]
        },
        "credit_and_debt": {
            "credit_cards": ["credit card", "statement", "billing cycle", "minimum payment", "credit limit", "apr"],
            "interest_and_repayment": ["interest rate", "compound interest", "repayment", "principal", "loan", "amortization"],
            "good_vs_bad_debt": ["good debt", "bad debt", "mortgage", "student loan", "payday loan", "high-interest debt"]
        },
        "risk_and_insurance": {
            "financial_risk": ["risk", "uncertainty", "volatility", "exposure", "hazard", "threat"],
            "insurance_basics": ["insurance", "premium", "deductible", "policy", "coverage", "claim"],
            "protection_planning": ["protection plan", "life insurance", "health insurance", "estate planning", "will"]
        },
        "investment_basics": {
            "risk_return": ["risk and return", "tradeoff", "yield", "reward", "profitability", "capital gain"],
            "simple_investing": ["stock", "bond", "mutual fund", "index fund", "brokerage", "dividend"],
            "diversification_basics": ["diversification", "portfolio", "asset allocation", "spread risk", "basket"]
        },
        "consumer_rights_and_financial_fraud": {
            "scam_awareness": ["scam", "fraud", "phishing", "ponzi", "pyramid", "identity theft"],
            "digital_finance_safety": ["password", "two-factor", "encryption", "secure connection", "cybersecurity", "online banking"],
            "consumer_protection": ["protection agency", "ombudsman", "consumer right", "dispute", "complaint", "refund"]
        }
    }

    # Complexity indicators
    HARD_INDICATORS = ["tradeoff", "opportunity cost", "arbitrage", "macroeconomics", "liquidity", "fiduciary", "yield curve", "amortization", "quantitative"]
    MEDIUM_INDICATORS = ["compare", "categorize", "practical example", "difference between", "versus", "scenario"]

    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        Executes the rule-based classification over the input text.
        """
        text_lower = text.lower()
        analyzed_chars = len(text)
        
        # 1. Score Topics & Subtopics
        topic_scores = {topic: 0 for topic in self.TAXONOMY.keys()}
        subtopic_scores = {topic: {sub: 0 for sub in self.TAXONOMY[topic].keys()} for topic in self.TAXONOMY.keys()}
        found_keywords = set()

        # Iterate taxonomy and count occurrences
        for topic, subtopics in self.TAXONOMY.items():
            for subtopic, keywords in subtopics.items():
                for kw in keywords:
                    # Look for whole word/phrase matches
                    matches = len(re.findall(rb"\\b" + kw.encode() + rb"\\b", text_lower.encode(), re.IGNORECASE))
                    if matches == 0 and kw in text_lower:
                        # Fallback for simple substring if \b fails on punctuation
                        matches = text_lower.count(kw)
                        
                    if matches > 0:
                        topic_scores[topic] += matches
                        subtopic_scores[topic][subtopic] += matches
                        found_keywords.add(kw)

        # 2. Determine Winning Topic
        winning_topic = None
        if max(topic_scores.values()) > 0:
            winning_topic = max(topic_scores, key=topic_scores.get) # type: ignore
        
        # 3. Determine Winning Subtopic
        winning_subtopic = None
        if winning_topic:
            winning_subtopic = max(subtopic_scores[winning_topic], key=subtopic_scores[winning_topic].get) # type: ignore

        # 4. Determine Difficulty
        hard_hits = sum(1 for kw in self.HARD_INDICATORS if kw in text_lower)
        medium_hits = sum(1 for kw in self.MEDIUM_INDICATORS if kw in text_lower)

        # Rules as per spec:
        if hard_hits >= 2 or (winning_topic == "investment_basics" and hard_hits >= 1):
            difficulty = "hard"
            rationale_diff = f"Classified as hard due to presence of complex terms ({hard_hits} hits) indicating tradeoffs or abstract reasoning."
        elif medium_hits >= 2 or (hard_hits == 1):
            difficulty = "medium"
            rationale_diff = f"Classified as medium due to presence of comparisons/practical terms ({medium_hits} hits)."
        else:
            difficulty = "easy"
            rationale_diff = "Classified as easy due to low concept density and focus on basic definitions."

        # Adjust for length proxy (long documents usually contain more density)
        if analyzed_chars > 20000 and difficulty == "easy":
            difficulty = "medium"
            rationale_diff += " Bumped to medium due to document length."

        # 5. Generate Candidate Learning Objective
        objective = None
        if winning_topic and winning_subtopic:
            # Format nicely for the output
            clean_topic = winning_topic.replace("_", " ").title()
            clean_sub = winning_subtopic.replace("_", " ").title()
            objective = f"Understand the core concepts of {clean_sub} within {clean_topic}. / เข้าใจแนวคิดหลักเรื่อง {clean_sub} ในบริบทของ {clean_topic}"
        else:
            objective = "Grasp the basic principles of Financial Literacy. / เข้าใจหลักการพื้นฐานของความรู้ทางการเงิน"

        # 6. Assemble output
        rationale = f"Document matched {len(found_keywords)} vocabulary terms. "
        if winning_topic:
            rationale += f"Scored highest in '{winning_topic}' -> '{winning_subtopic}'. "
        else:
            rationale += "No strong topic matches found; defaulting to unclassified. "
            
        rationale += rationale_diff

        return {
            "topic": winning_topic,
            "subtopic": winning_subtopic,
            "difficulty": difficulty,
            "learning_objective": objective,
            "keywords_found": list(found_keywords),
            "rationale": rationale,
            "analyzed_char_count": analyzed_chars
        }
