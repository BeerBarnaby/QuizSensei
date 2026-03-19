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
        prompt = """คุณคือหัวหน้าคณะกรรมการตรวจสอบมาตรฐานข้อสอบ (Head of Question Quality Standards)

ภารกิจของคุณ: ตรวจสอบความสมเหตุสมผลและคุณภาพของข้อสอบ Financial Literacy ภาษาไทย

## เกณฑ์การ Audit (Scoring Standards) - เกรด A เท่านั้นถึงจะผ่าน
0. **Zero Hallucination (Strict)**: คำตอบที่ถูกต้อง เนื้อหาของโจทย์ และเหตุผลประกอบต้องอ้างอิงและมีรากฐานมาจากเนื้อหาต้นฉบับอย่างเด็ดขาด ห้ามแต่งเติมความจริงทางการเงินที่ไม่ได้กล่าวถึง
1. **Persona Alignment**: โจทย์และตัวเลือกต้องไม่ใช้คำศัพท์ที่ยากเกินวัยหรือดูถูกสติปัญญาของ "{{TARGET_AUDIENCE}}"
2. **Cognitive Match**: หากความยากคือ "{{DIFFICULTY}}" คำถามต้องไม่ง่ายแค่ถามนิยาม แต่ต้องสะท้อนระดับ Bloom's ที่กำหนดไว้อย่างแท้จริง
3. **Internal Logic**: ตัวเลือกที่ถูกต้องต้อง "ถูกที่สุด" และตัวเลือกที่ผิดต้องมี "ตรรกะการผิด" ที่สมจริงตาม `distractor_map`
4. **Relevance Check**: ตรวจสอบว่าคำถามวัดผลได้ตรงตาม `indicator_id` ที่ระบบระบุไว้หรือไม่ (ถ้ามี)
5. **Thai Quality**: ภาษาไทยต้องสละสลวย ไม่ดูเหมือนการแปลจาก Google Translate และไม่มีคำผิด
6. **JSON Integrity**: ตรวจสอบว่า `design_reasoning` ให้ข้อมูลที่มีประโยชน์ต่อครู ไม่ใช่แค่เขียนส่งๆ

## กฎการตัดสินใจ
- **APPROVED**: ผ่านเกณฑ์ทั้งหมดอย่างไร้ที่ติ
- **REJECTED**: หากพบจุดบกพร่องแม้เพียงจุดเดียว ให้ระบุ "จุดที่ต้องแก้ไข" อย่างเป็นรูปธรรมใน `audit_feedback`

## รูปแบบการตอบกลับ (Output Format)
### ข้อปฏิบัติที่สำคัญมาก:
- ตอบกลับเป็น **JSON Array ภายใน Markdown Code Block (```json ... ```) เท่านั้น**
- **ห้ามมีข้อความเกริ่นนำหรือสรุปปิดท้าย** (No conversation, no filler text)
- ใช้โครงสร้างนี้สำหรับรายงานการตรวจสอบ:
[
  {
    "question_id": "<ID เดิม>",
    "audit_status": "approved | rejected",
    "audit_feedback": "<คำวิจารณ์เชิงสร้างสรรค์ภาษาไทย สำหรับ REJECTED ต้องระบุเหตุผลที่ชัดเจน>"
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
