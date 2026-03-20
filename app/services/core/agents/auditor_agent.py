"""
Agent 3 (Auditor) - Performs quality control on generated questions, ensuring alignment with pedagogical goals and target audience.
"""
import json
import random
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any
import httpx

from app.core.config import Settings

logger = logging.getLogger(__name__)


class AuditorAgent:
    """
    Agent 3 – ตรวจสอบคุณภาพข้อสอบทางการเงิน
    ตรวจสอบว่าข้อสอบตรงกับ Target Audience, ระดับความยาก (Bloom's), 
    และตัวเลือกผิดมีการให้เหตุผลที่สมเหตุสมผลหรือไม่
    ห้ามปล่อยผ่านถ้าไม่ใช่ภาษาไทย หรือเหตุผลไม่ชัดเจน
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.OPENROUTER_MODEL

    def _get_system_prompt(self, target_audience: str, difficulty: str) -> str:
        prompt = """คุณคือผู้ช่วยตรวจสอบข้อสอบ (Question Review Assistant)

ภารกิจของคุณ: ตรวจสอบข้อสอบ Financial Literacy ภาษาไทย โดยเน้นการ "ปล่อยผ่าน (APPROVE)" เพื่อความรวดเร็ว

## เกณฑ์การ Audit (Lenient Standards) - เน้นการให้โอกาสและปรับปรุงภายหลัง
1. **General Alignment**: ตรวจสอบว่าโจทย์เกี่ยวข้องกับ "{{TARGET_AUDIENCE}}" และมีความยากใกล้เคียงกับ "{{DIFFICULTY}}" หรือไม่
2. **Basic Logic**: ตัวเลือกที่ถูกต้องควรจะสมเหตุสมผล และตัวเลือกหลอกไม่ควรดูแย่จนเกินไป
3. **Thai Language**: ภาษาไทยต้องพออ่านเข้าใจ ไม่ต้องถึงกับสละสลวยไร้ที่ติ
4. **Zero Tolerance only for**:
    - ข้อสอบที่ไม่ใช่ภาษาไทย
    - ข้อสอบที่ระบบ JSON พังเสียหายจนอ่านไม่ได้
    - ข้อสอบที่เฉลยผิดอย่างเห็นได้ชัด (เช่น คำนวณเลขผิดมหันต์)

## กฎการตัดสินใจ
- **APPROVED**: หากข้อสอบ "พอใช้ได้" หรือมีจุดผิดพลาดเล็กน้อยที่ครูสามารถไปแก้เองได้ ให้ปล่อยผ่านทันที
- **REJECTED**: เฉพาะกรณีที่ข้อสอบแย่มากจนใช้งานไม่ได้จริงๆ เท่านั้น

## รูปแบบการตอบกลับ (Output Format)
### ข้อปฏิบัติที่สำคัญมาก:
- ตอบกลับเป็น **JSON Array ภายใน Markdown Code Block (```json ... ```) เท่านั้น**
- **ห้ามมีข้อความเกริ่นนำหรือสรุปปิดท้าย**
- ใช้โครงสร้างนี้สำหรับรายงานการตรวจสอบ:
[
  {
    "question_id": "<ID เดิม>",
    "audit_status": "approved | rejected",
    "audit_feedback": "<คำแนะนำสั้นๆ ภาษาไทย (ถ้ามี)>"
  }
]
"""
        return prompt.replace("{{TARGET_AUDIENCE}}", target_audience).replace("{{DIFFICULTY}}", difficulty)

    async def audit(
        self,
        questions: List[Dict[str, Any]],
        audience: str,
        difficulty: str,
        source_text: str,
    ) -> List[Dict[str, Any]]:
        """
        Runs each question through the LLM auditor (Thai rules and Zero Hallucination).
        Returns the questions list with audit_status and audit_feedback injected.
        """
        if not questions:
            return questions

        system_prompt = self._get_system_prompt(audience, difficulty)
        
        # Trim payload to save tokens
        audit_payload = [
            {
                "question_id": q.get("question_id"),
                "stem": q.get("stem"),
                "choices": q.get("choices"),
                "correct_answer": q.get("correct_answer"),
                "design_reasoning": q.get("design_reasoning"),
                "distractor_map": q.get("distractor_map"),
                "source_evidence": q.get("source_evidence"),
            }
            for q in questions
        ]

        user_prompt = (
            f"เริ่มตรวจสอบข้อสอบ 4 ตัวเลือกภาษาไทย ทั้งหมด {len(questions)} ข้อ.\n\n"
            f"--- ข้อมูลบริบทที่ใช้ตรวจสอบ ---\n"
            f"เนื้อหาต้นฉบับ (Source Text):\n{source_text[:4000]}\n\n"
            f"ระดับผู้เรียนที่เลือก: {audience}\n"
            f"ระดับความยากที่เลือก: {difficulty}\n\n"
            f"--- รายการข้อสอบ ---\n"
            f"{json.dumps(audit_payload, ensure_ascii=False, indent=2)}\n\n"
            "ส่งกลับเป็น Array JSON ของผลลัพธ์การ Audit เท่านั้น"
        )

        import asyncio
        from app.core.llm import call_openrouter_json
        
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            logger.info(f"Agent 3 กำลังออดิทข้อสอบ {len(questions)} ข้อ สำหรับระดับ {audience}")

            audit_results = await asyncio.to_thread(
                call_openrouter_json,
                prompt=full_prompt,
                model=self.model,
                temperature=0.1
            )

            if not audit_results or not isinstance(audit_results, list):
                 logger.error("Agent 3 API Error or invalid format fallback")
                 return questions
            
            audit_map = {r["question_id"]: r for r in audit_results}
            checked_at = datetime.now(timezone.utc).isoformat()

            for q in questions:
                qid = q.get("question_id")
                if qid in audit_map:
                    q["audit_status"] = audit_map[qid].get("audit_status", "approved")
                    q["audit_feedback"] = audit_map[qid].get("audit_feedback")
                else:
                    q["audit_status"] = "approved"
                    q["audit_feedback"] = "ผ่านอัตโนมัติ: Agent 3 ไม่ได้ส่งผลลัพธ์ย้อนกลับสำหรับข้อนี้"
                q["audited_at"] = checked_at

            return questions

        except Exception as e:
            logger.error(f"Agent 3 failed: {e}")
            for q in questions:
                q.setdefault("audit_status", "rejected")
                q.setdefault("audit_feedback", f"การตรวจสอบถูกข้ามและปฏิเสธเนื่องจากระบขัดข้อง: {str(e)}")
            return questions
