"""
app/services/agents/grader_agent.py

Agent 4: Answer Grader.
Diagnoses student answers using the distractor_map produced by Agent 2.
Fully in Thai.
"""

import logging
from typing import Dict, Any, Optional

from app.schemas.agent_outputs import GraderOutput

logger = logging.getLogger(__name__)


class GraderAgent:
    """
    Agent 4 – ประเมินระบบคำตอบแบบวินิจฉัย (Zero-cost diagnostic)
    อ่านค่า distractor_map ภาษาไทยจากฐานข้อมูลมาแสดงทันทีที่ผู้เรียนตอบ
    """

    def grade(
        self,
        question_payload: Dict[str, Any],
        selected_key: str,
    ) -> GraderOutput:
        question_id = question_payload.get("question_id", "unknown")
        correct_answer = question_payload.get("correct_answer", "")
        selected_key_upper = selected_key.upper()
        is_correct = selected_key_upper == correct_answer.upper()

        if is_correct:
            return GraderOutput(
                question_id=question_id,
                is_correct=True,
                correct_answer=correct_answer,
                misconception_identified=None,
                diagnostic_message=self._build_correct_message(question_payload),
                suggested_review_topic=None,
            )

        # ── Wrong answer: extract diagnostic info from distractor_map ─────
        distractor_map: Dict[str, Any] = question_payload.get("distractor_map", {})
        distractor_info = distractor_map.get(selected_key_upper, {})

        misconception      = distractor_info.get("misconception")
        why_plausible      = distractor_info.get("why_plausible")
        diagnostic_meaning = distractor_info.get("diagnostic_meaning")
        suggested_topic    = distractor_info.get("suggested_review_topic")

        # Fall back to legacy rationale field if distractor_map is incomplete
        basic_rationale = question_payload.get(
            "rationale_for_incorrect_choices",
            "คำตอบของคุณไม่ถูกต้อง โปรดทบทวนเนื้อหาอีกครั้ง"
        )
        if why_plausible:
            basic_rationale += f"\n(เหตุผลที่มักสับสน: {why_plausible})"

        diagnostic_message = self._build_diagnostic_message(
            correct_answer=correct_answer,
            correct_rationale=question_payload.get("rationale_for_correct_answer", ""),
            basic_rationale=basic_rationale
        )

        return GraderOutput(
            question_id=question_id,
            is_correct=False,
            correct_answer=correct_answer,
            misconception_identified=misconception, # Keep for future analytics
            diagnostic_message=diagnostic_message,
            suggested_review_topic=suggested_topic,
        )

    def _build_correct_message(self, payload: Dict[str, Any]) -> str:
        rationale = payload.get("rationale_for_correct_answer", "")
        msg = f"✓ ถูกต้อง!"
        if rationale:
            msg += f"\nเหตุผล: {rationale}"
        return msg

    def _build_diagnostic_message(
        self,
        correct_answer: str,
        correct_rationale: str,
        basic_rationale: str,
    ) -> str:
        parts = [f"✗ ยังไม่ถูกต้อง (คำตอบที่ถูกคือข้อ {correct_answer})"]
        if basic_rationale:
            parts.append(f"\n💡 คำอธิบาย: {basic_rationale}")
        if correct_rationale:
            parts.append(f"\n📚 หลักการที่ถูกต้อง: {correct_rationale}")
        return "\n".join(parts)
