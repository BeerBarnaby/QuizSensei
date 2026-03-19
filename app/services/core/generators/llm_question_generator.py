"""
Agent 2 (Generator) - Generates structured financial literacy questions with diagnostic distractors based on source text.
"""
import json
import random
import uuid
import logging
from typing import List, Dict, Any

from app.core.config import Settings
from app.services.core.generators.base import BaseQuestionGenerator
from app.schemas.teacher.question import QuestionGenerationRequest

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
        """
        Maps the UI difficulty (Easy/Medium/Hard) to specific Cognitive Levels in Bloom's Taxonomy.
        This forces the LLM to design stems that test different levels of thinking.
        """
        diff_lower = (difficulty or "ปานกลาง").lower()
        if diff_lower == "ง่าย":
            # Level 1-2: Memorization and Basic understanding
            return "การจำ/ความเข้าใจ (Remember / Understand): คำถามวัดความจำนิยาม กฎพื้นฐาน หรือการอธิบายความหมายตรงๆ"
        elif diff_lower == "ยาก":
            # Level 4-6: Higher order thinking
            return "การวิเคราะห์/ประเมินค่า/สร้างสรรค์ (Analyze / Evaluate / Create): คำถามวัดการตัดสินใจเลือกทางเลือกที่ดีที่สุด การจัดลำดับความสำคัญ หรือการออกแบบแผนการเงิน ภายใต้ข้อจำกัดหลายอย่าง"
        else: # ปานกลาง
            # Level 3-4: Application and Analysis
            return "การประยุกต์ใช้/วิเคราะห์ (Apply / Analyze): คำถามวัดการนำไปใช้ในสถานการณ์จำลอง การคำนวณ การเปรียบเทียบ หรือหาความสัมพันธ์ของตัวแปร"

    def _get_system_prompt(self, topic: str, subtopic: str, difficulty: str, target_audience: str, num_q: int, blooms_rule: str, indicator_str: str) -> str:
        prompt = """คุณคือมาสเตอร์ด้านการออกแบบข้อสอบ (Master Question Designer) ที่เชี่ยวชาญด้าน Financial Literacy โดยเฉพาะ

ภารกิจของคุณ: สร้างข้อสอบแบบปรนัยจำนวน {{NUM_Q}} ข้อ ที่มีคุณภาพสูงและสามารถ "วินิจฉัย" จุดอ่อนของผู้เรียนได้

{{INDICATORS}}

## 1. ข้อกำหนดสำหรับโจทย์ชุดนี้
- **หัวข้อ**: {{TOPIC}} ({{SUBTOPIC}})
- **กลุ่มเป้าหมาย**: {{TARGET_AUDIENCE}} (ใช้ระดับภาษาและสถานการณ์จำลองที่วัยนี้เข้าถึงได้จริง)
- **ระดับสติปัญญา (Bloom's Taxonomy)**: {{DIFFICULTY}} — {{BLOOMS_RULE}}

## 2. หลักการสร้าง "โจทย์จำลองวิถีชีวิต" (Scenario-based)
- อย่าเน้นแค่การถามนิยามตรงๆ (เช่น "X คืออะไร?") 
- ให้สร้าง **สถานการณ์จำลอง (Scenario)** ให้ผู้เรียนต้องใช้ความรู้ในการแก้ปัญหาหรือตัดสินใจ
- สำหรับ 'วัยทำงาน' ให้เน้นเคสจริงในออฟฟิศ การบริหารหนี้ หรือการลงทุน
- สำหรับ 'ประถม/มัธยม' ให้เน้นเคสค่าขนม การซื้อของเล่น หรือกติกาในครอบครัว

## 3. กฎทองของตัวเลือกหลอก (Diagnostic Distractors)
ตัวเลือกที่ผิดทั้ง 3 ข้อ ต้องมี "ความหมายเชิงวินิจฉัย":
- **ต้องมาจากความเข้าใจผิด (Misconception)** ที่พบบ่อย: เช่น สับสนระหว่าง "ออมก่อนใช้" กับ "ใช้เหลือค่อยออม"
- **ต้องน่าดึงดูด (Plausible)**: สำหรับคนที่ยังไม่แม่นเนื้อหาหรือคิดตรรกะแบบผิวเผิน
- **ต้องตรวจแก้ได้ (Actionable)**: บอกได้ว่าถ้าตอบข้อนี้ แสดงว่าผู้เรียนขาดความรู้เรื่องใดเป็นพิเศษ

## 4. รูปแบบ JSON (Output Format)
### ข้อปฏิบัติที่สำคัญมาก:
- ตอบกลับเป็น **JSON Array ภายใน Markdown Code Block (```json ... ```) เท่านั้น**
- **ห้ามมีข้อความเกริ่นนำหรือสรุปปิดท้าย** (No conversation, no filler text)
- ตรวจสอบว่าโจทย์ทุกข้ออยู่ใน Array เดียวกัน
- ใช้โครงสร้างนี้สำหรับแต่ละข้อ:
[
  {
    "question_id": "AUTOGEN",
    "topic": "{{TOPIC}}",
    "subtopic": "{{SUBTOPIC}}",
    "indicator_id": "<ID ของตัวชี้วัดที่ข้อนี้วัดผล เช่น IND-01>",
    "target_audience_level": "{{TARGET_AUDIENCE}}",
    "difficulty": "{{DIFFICULTY}}",
    "question_type": "multiple_choice",
    "stem": "<โจทย์/สถานการณ์จำลอง ภาษาไทย>",
    "choices": [
      {"key": "A", "text": "<เนื้อหาตัวเลือก>"},
      {"key": "B", "text": "<เนื้อหาตัวเลือก>"},
      {"key": "C", "text": "<เนื้อหาตัวเลือก>"},
      {"key": "D", "text": "<เนื้อหาตัวเลือก>"}
    ],
    "correct_answer": "<A/B/C/D>",
    "rationale_for_correct_answer": "<เหตุผลเชิงวิชาการภาษาไทย>",
    "rationale_for_incorrect_choices": "<คำอธิบายสรุปรวมๆ ว่าทำไมข้ออื่นถึงไม่ถูกต้อง>",
    "design_reasoning": "<อธิบายว่าคำถามนี้วัดผล Bloom's ตามที่ระบุไว้อย่างไร>",
    "distractor_map": {
      "<Key ข้อที่ผิด>": {
        "misconception": "<ชื่อย่อความเข้าใจผิด>",
        "why_plausible": "<ทำไมคนถึงเลือกผิดข้อนี้>",
        "diagnostic_meaning": "<บทสรุปว่านักเรียนขาดความรู้เรื่องใด>",
        "suggested_review_topic": "<หัวข้อที่ต้องทบทวน>"
      }
    },
    "misconception_tags": ["tag1", "tag2"],
    "source_evidence": "<อ้างอิงจากเนื้อหาต้นฉบับ>",
    "why_this_question": "<ความภูมิใจในการออกแบบข้อนี้>",
    "audit_status": "pending",
    "status": "draft"
  }
]
"""
        return (prompt
            .replace("{{NUM_Q}}", str(num_q))
            .replace("{{INDICATORS}}", indicator_str)
            .replace("{{TOPIC}}", topic)
            .replace("{{SUBTOPIC}}", subtopic)
            .replace("{{TARGET_AUDIENCE}}", target_audience)
            .replace("{{DIFFICULTY}}", difficulty)
            .replace("{{BLOOMS_RULE}}", blooms_rule))

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

        # Use filtered indicators from analysis object
        indicators = analysis.get("indicators", [])

        # Generate formatting strings
        blooms_rule = self._map_difficulty_to_blooms(difficulty)
        indicator_str = ""
        if indicators:
            indicator_str = "## 0. ตัวชี้วัดที่ต้องเน้น (Priority Indicators)\n" + "\n".join([f"- {ind['id']}: {ind['text']}" for ind in indicators])

        system_prompt = self._get_system_prompt(topic, subtopic, difficulty, audience, num_q, blooms_rule, indicator_str)
        user_prompt = (
            f"เริ่มสร้างข้อสอบจำนวน {num_q} ข้อ โดยใช้เนื้อหาอ้างอิงด้านล่างนี้:\n\n"
            f"--- แหล่งข้อมูลอ้างอิง ---\n{text[:4000]}\n--- สิ้นสุดแหล่งข้อมูล ---\n\n"
            "อย่าลืมตอบกลับด้วยรูปแบบ JSON รูปแบบข้อสอบตามที่กำหนดเท่านั้น"
        )

        import asyncio
        from app.core.llm import call_openrouter_json
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            logger.info("============== AGENT 2 PROMPT START ==============")
            logger.info(full_prompt)
            logger.info("============== AGENT 2 PROMPT END ==============")
            logger.info(f"Agent 2 เริ่มสร้างข้อสอบ {num_q} ข้อสำหรับระดับ {audience} ความยาก {difficulty}")

            questions = await asyncio.to_thread(
                call_openrouter_json,
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
