"""
app/services/generators/llm_question_generator.py

Agent 2: Financial Literacy Question Generator.
Uses OpenRouter LLM to generate deeply-justified multiple-choice questions in Thai.
Respects Audience Level and maps arbitrary easy/medium/hard difficulty to Bloom's taxonomy.
"""

import json
import random
import uuid
import logging
from typing import List, Dict, Any
import httpx

from app.core.config import Settings
from app.services.generators.base import BaseQuestionGenerator
from app.schemas.question import QuestionGenerationRequest

logger = logging.getLogger(__name__)


class LLMQuestionGenerator(BaseQuestionGenerator):
    """
    Agent 2 – สร้างข้อสอบทางการเงินเป็นภาษาไทย
    - รองรับ 5 กลุ่มเป้าหมาย
    - แมปความยาก (ง่าย/ปานกลาง/ยาก) เป็น Bloom's Taxonomy
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.OPENROUTER_MODEL

    def _map_difficulty_to_blooms(self, difficulty: str) -> str:
        """แปลงความยากที่รับมาจาก UI เป็นทักษะและคำสั่งย่อยตามทฤษฎี Bloom"""
        diff_lower = (difficulty or "ปานกลาง").lower()
        if diff_lower == "ง่าย":
            return "การจำ/ความเข้าใจ (Remember / Understand): คำถามวัดความจำนิยาม กฎพื้นฐาน หรือการอธิบายความหมายตรงๆ"
        elif diff_lower == "ยาก":
            return "การวิเคราะห์/ประเมินค่า/สร้างสรรค์ (Analyze / Evaluate / Create): คำถามวัดการตัดสินใจเลือกทางเลือกที่ดีที่สุด การจัดลำดับความสำคัญ หรือการออกแบบแผนการเงิน ภายใต้ข้อจำกัดหลายอย่าง"
        else: # ปานกลาง
            return "การประยุกต์ใช้/วิเคราะห์ (Apply / Analyze): คำถามวัดการนำไปใช้ในสถานการณ์จำลอง การคำนวณ การเปรียบเทียบ หรือหาความสัมพันธ์ของตัวแปร"

    def _get_system_prompt(self, topic: str, subtopic: str, difficulty: str, target_audience: str, num_q: int) -> str:
        blooms_rule = self._map_difficulty_to_blooms(difficulty)
        
        return f"""คุณคือ Agent 2 ของระบบ QuizSensei หน้าที่ของคุณคือการสร้างข้อสอบวิชา Financial Literacy (ภาษาไทย 100%)

สร้างข้อสอบแบบปรนัย (Multiple Choice) จำนวน {num_q} ข้อ ในหัวข้อ:
  Topic:    {topic}
  Subtopic: {subtopic}

## 1. บริบทเฉพาะสำหรับข้อสอบชุดนี้
- **กลุ่มเป้าหมาย (Target Audience)**: {target_audience} 
  (กรุณาใช้บริบท สถานการณ์จำลอง ชื่อตัวละคร และภาษาให้เหมาะสมกับวัยนี้ที่สุด ห้ามใช้ภาษาที่เด็กเกินไปหรือผู้ใหญ่เกินไป)
- **ระดับความยาก และ Bloom's Taxonomy**: {difficulty} — {blooms_rule}
  (ลักษณะของคำถามต้องเป็นไปตามทฤษฎีการเรียนรู้นี้)

## 2. กฎการออกแบบตัวเลือกที่ผิด (Diagnostic Design Rules)
ทุกตัวเลือกที่ผิด (จากตัวเลือกทั้งหมด 4 ข้อ) ต้อง:
1. ไม่ง่ายเกินไปจนเดาตัดทิ้งได้ง่ายๆ
2. ต้องมาจาก **ความเข้าใจผิดทางการเงิน (Misconception)** ที่พบได้บ่อยในกลุ่มเป้าหมายนี้
3. อธิบายได้ว่า ทำไมผู้เข้าสอบที่ยังไม่แม่นเนื้อหาถึงเลือกข้อนี้

## 3. รูปแบบ Output
ส่งคืนผลลัพธ์เป็นอาเรย์ JSON เท่านั้น ห้ามมีข้อความอื่นหรือ Markdown
[
  {{
    "question_id": "AUTOGEN",
    "topic": "{topic}",
    "subtopic": "{subtopic}",
    "target_audience_level": "{target_audience}",
    "difficulty": "{difficulty}",
    "question_type": "multiple_choice",
    "stem": "<โจทย์คำถามหรือสถานการณ์จำลองที่ตั้งขึ้น อิงบริบทกลุ่มเป้าหมาย>",
    "choices": [
      {{"key": "A", "text": "<ตัวเลือก A>"}},
      {{"key": "B", "text": "<ตัวเลือก B>"}},
      {{"key": "C", "text": "<ตัวเลือก C>"}},
      {{"key": "D", "text": "<ตัวเลือก D>"}}
    ],
    "correct_answer": "<A|B|C|D>",
    "rationale_for_correct_answer": "<เหตุผลว่าทำไมคำตอบนี้ถึงถูกต้อง อิงหลักการทางการเงิน>",
    "rationale_for_incorrect_choices": "<คำอธิบายรวมๆ ทำไมข้ออื่นถึงผิด>",
    "design_reasoning": "<เหตุผลที่เลือกใช้คำถามนี้ มันวัดผลอะไรและตรงกับความยาก/Bloom's ตามที่ขออย่างไร>",
    "distractor_map": {{
      "<คีย์ข้อที่ผิด 1>": {{
        "misconception": "<แท็กชื่อความเข้าใจผิด เช่น 'ลืมหักเงินออมก่อนใช้'>",
        "why_plausible": "<ทำไมคนถึงมักตอบข้อนี้>",
        "diagnostic_meaning": "<ข้อสรุปเชิงวินิจฉัย เช่น 'ผู้เรียนไม่เข้าใจสมการเงินออมที่ถูกต้อง'>",
        "suggested_review_topic": "<หัวข้อเรื่องย่อยที่ควรกลับไปอ่าน>"
      }},
      "<คีย์ข้อที่ผิด 2>": {{ ... }},
      "<คีย์ข้อที่ผิด 3>": {{ ... }}
    }},
    "misconception_tags": ["<แท็ก 1>", "<แท็ก 2>"],
    "source_evidence": "<อ้างอิงเนื้อหาต้นฉบับที่เอามาออกข้อสอบ>",
    "why_this_question": "<จดบันทึกย่อว่าข้อสอบนี้เยี่ยมอย่างไร>",
    "audit_status": "pending",
    "audit_feedback": null,
    "status": "draft"
  }}
]
"""

    async def generate(
        self,
        text: str,
        analysis: Dict[str, Any],
        request: QuestionGenerationRequest,
    ) -> List[Dict[str, Any]]:
        """Agent 2 pipeline: generate {n} questions with full justification in Thai."""
        topic      = request.topic_filter      or analysis.get("topic", "budgeting_and_spending")
        subtopic   = request.subtopic_filter   or analysis.get("subtopic", "needs_vs_wants")
        difficulty = request.difficulty_filter or "ปานกลาง"
        audience   = request.target_audience_level
        num_q      = request.number_of_questions

        system_prompt = self._get_system_prompt(topic, subtopic, difficulty, audience, num_q)
        user_prompt = (
            f"เริ่มสร้างข้อสอบจำนวน {num_q} ข้อ โดยใช้เนื้อหาอ้างอิงด้านล่างนี้:\n\n"
            f"--- แหล่งข้อมูลอ้างอิง ---\n{text[:4000]}\n--- สิ้นสุดแหล่งข้อมูล ---\n\n"
            "อย่าลืมตอบกลับด้วยรูปแบบ JSON รูปแบบข้อสอบตามที่กำหนดเท่านั้น"
        )

        from app.core.llm import call_openrouter_json
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            logger.info(f"Agent 2 เริ่มสร้างข้อสอบ {num_q} ข้อสำหรับระดับ {audience} ความยาก {difficulty}")

            questions = call_openrouter_json(
                prompt=full_prompt,
                model=self.model,
                temperature=0.7
            )
            
            if not questions:
                logger.error("Agent 2 failed to get valid JSON questions")
                raise Exception("Agent 2 ล้มเหลวเนื่องจากการเชื่อมต่อ API หรือการประมวลผล JSON")

            if not isinstance(questions, list):
                questions = [questions]

            for q in questions:
                if q.get("question_id") in ("AUTOGEN", "", None):
                    q["question_id"] = f"q_{uuid.uuid4().hex[:8]}"
                q.setdefault("audit_status", "pending")
                q.setdefault("audit_feedback", None)
                q.setdefault("distractor_map", {})
                q.setdefault("design_reasoning", "")
                q["target_audience_level"] = audience
                q["difficulty"] = difficulty

            return questions

        except Exception as e:
            logger.error(f"Agent 2 ใช้งาน LLM ล้มเหลว: {e}")
            raise Exception(f"Agent 2 ทำงานผิดพลาด: {str(e)}")
