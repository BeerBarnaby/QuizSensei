"""
Specialized generator for Financial Literacy questions.
Extends base generation logic with domain-specific constraints for FL education.
Maps incorrect options to specific financial misconceptions.
"""
import json
import uuid
from typing import List, Dict, Any

from app.services.generators.base import BaseQuestionGenerator
from app.schemas.question import QuestionGenerationRequest

class FinancialLiteracyQuestionGenerator(BaseQuestionGenerator):
    """
    Diagnostic generator mapping incorrect choices to explicit misconceptions
    such as 'confuses_needs_and_wants' and 'ignores_interest_cost'.
    """

    # Pre-defined diagnostic templates for the MVP
    DIAGNOSTIC_TEMPLATES = {
        "budgeting_and_spending": {
            "misconceptions": [
                "confuses_needs_and_wants",
                "cannot_distinguish_fixed_and_variable_expenses",
                "ignores_long_term_financial_goal"
            ],
            "stems": [
                "When creating a monthly budget, which of the following represents the MOST critical first step?",
                "If an individual must reduce monthly spending immediately, which category should they target first?"
            ]
        },
        "saving_and_emergency_fund": {
            "misconceptions": [
                "misunderstands_emergency_fund_purpose",
                "underestimates_financial_risk",
                "ignores_long_term_financial_goal"
            ],
            "stems": [
                "What is the primary purpose of maintaining an emergency fund?",
                "How does delayed gratification directly impact long-term savings?"
            ]
        },
        "credit_and_debt": {
            "misconceptions": [
                "thinks_credit_is_extra_income",
                "ignores_interest_cost",
                "does_not_compare_options"
            ],
            "stems": [
                "When comparing two credit cards, which factor has the largest impact on long-term debt if a balance is carried?",
                "Why is paying only the minimum balance on a credit card financially dangerous?"
            ]
        }
    }

    async def generate(
        self, 
        text: str, 
        analysis: Dict[str, Any], 
        request: QuestionGenerationRequest
    ) -> List[Dict[str, Any]]:
        """
        Generates diagnostic question drafts based on requested filters and source analysis.
        """
        
        # Apply filters or fallback to analysis defaults
        topic = request.topic_filter or analysis.get("topic", "budgeting_and_spending")
        subtopic = request.subtopic_filter or analysis.get("subtopic", "unknown")
        difficulty = request.difficulty_filter or analysis.get("difficulty", "medium")
        num_q = request.number_of_questions

        # Fetch templates for this topic (or fallback to budgeting)
        templates = self.DIAGNOSTIC_TEMPLATES.get(topic, self.DIAGNOSTIC_TEMPLATES["budgeting_and_spending"])
        misconceptions = templates["misconceptions"]
        stems = templates["stems"]

        questions = []
        for i in range(num_q):
            # Rotate stems to simulate variety
            stem = stems[i % len(stems)]
            
            # Map specific misconceptions to incorrect choices
            qstr = {
                "question_id": f"q_{uuid.uuid4().hex[:8]}",
                "topic": topic,
                "subtopic": subtopic,
                "difficulty": difficulty,
                "question_type": "multiple_choice",
                "stem": stem,
                "choices": [
                    {"key": "A", "text": "This choice represents taking on unnecessary debt without calculation."},
                    {"key": "B", "text": "This is the financially sound and correct approach outlined in the text."},
                    {"key": "C", "text": "This choice confuses a luxury want for a baseline survival need."},
                    {"key": "D", "text": "This choice focuses only on the short term, ignoring compound interest."}
                ],
                "correct_answer": "B",
                "rationale_for_correct_answer": "Choice B correctly aligns with fundamental financial literacy principles regarding risk and cost reduction.",
                "rationale_for_incorrect_choices": "A ignores interest. C confuses needs and wants. D ignores long-term goals.",
                "misconception_tags": misconceptions,
                "source_evidence": text[:150] + "..." if len(text) > 150 else "N/A",
                "why_this_question": f"Diagnostic check mapping to {misconceptions[0]} and {misconceptions[1]}.",
                "status": "draft"
            }
            questions.append(qstr)

        return questions
