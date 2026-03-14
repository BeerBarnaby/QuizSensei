"""
app/services/agents/auditor_agent.py

Agent 3: Question Quality Auditor.
Reviews questions produced by Agent 2. 
Ensures Audience level, Bloom's difficulty map, and Thai language are respected.
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
        self.api_key = random.choice(settings.openrouter_keys_list) if settings.openrouter_keys_list else "dummy"

    def _get_system_prompt(self, target_audience: str, difficulty: str) -> str:
        return f"""คุณคือ Agent 3 ของระบบ EvalMind — ผู้ตรวจสอบคุณภาพข้อสอบ (Question Quality Auditor)

คุณจะได้รับรายการข้อสอบ Financial Literacy แบบปรนัย (Multiple Choice) ที่สร้างโดย Agent 2 (เป็นภาษาไทย)
หน้าที่ของคุณ: ประเมินข้อสอบแต่ละข้อว่าจะ "ผ่าน (APPROVED)" หรือ "ไม่ผ่าน (REJECTED)"

## เกณฑ์การประเมิน (Audit Criteria)
ข้อสอบแต่ละข้อต้องผ่านเกณฑ์ *ทั้งหมด* ต่อไปนี้:

1. **ระดับภาษาและกลุ่มเป้าหมาย**: ภาษา บริบท และตัวอย่างที่ใช้ต้องสอดคล้องกับ "{target_audience}"
2. **ระดับความท้าทาย (Difficulty -> Bloom's)**: ความซับซ้อนของคำถามต้องตอบโจทย์ความยากระดับ "{difficulty}"
3. **การออกแบบและเหตุผล (Design Reasoning)**: มีคำอธิบาย `design_reasoning` ที่ชัดเจนว่าทำไมคำถามนี้จึงสำคัญ
4. **คุณภาพตัวเลือกที่ผิด (Distractor Quality)**:
   - แต่ละตัวเลือกที่ผิดใน `distractor_map` มีการระบุความเข้าใจผิด (`misconception`) ที่ชัดแจ้ง
   - เหตุผลที่คนจะเลือกผิด (`why_plausible`) ฟังดูสมเหตุสมผลกับนักเรียนที่ยังไม่เข้าใจเนื้อหานี้
   - การวินิจฉัย (`diagnostic_meaning`) บอกได้ว่านักเรียนมีปัญหาเรื่องใด
5. **ความเป็นภาษาไทย 100%**: เนื้อหาคำถาม ตัวเลือก และคำอธิบายทั้งหมดต้องเป็นภาษาไทย (เว้นแต่ศัพท์เฉพาะทาง)

## กฎการตัดสินใจ
- ถ้าระบุว่า APPROVED: ต้องผ่านทั้ง 5 เกณฑ์ข้างต้น
- ถ้าระบุว่า REJECTED: ให้คำแนะนำจำเพาะเจาะจงว่าส่วนใดที่ต้องแก้ไข (เช่น "ภาษาทางการเกินไปสำหรับประถม" หรือ "ความเข้าใจผิดกว้างเกินไป")

## รูปแบบ Output (ตอบกลับเป็น JSON Array ควบคุมด้วย [] เท่านั้น ห้ามมีอาร์เรย์ซ้อนทับ หรือคำอื่นนอกเหนือจาก JSON)
[
  {{
    "question_id": "<ใช้ question_id เดิมจากที่ได้รับ>",
    "audit_status": "approved",
    "audit_feedback": "<คำชมเชิงประเมินคุณภาพสั้นๆ>"
  }},
  {{
    "question_id": "<id>",
    "audit_status": "rejected",
    "audit_feedback": "<ระบุข้อบกพร่องชัดเจนเพื่อไปสร้างข้อสอบเนื้อหานี้ใหม่>"
  }}
]
"""

    async def audit(
        self,
        questions: List[Dict[str, Any]],
        audience: str,
        difficulty: str,
    ) -> List[Dict[str, Any]]:
        """
        Runs each question through the LLM auditor (Thai rules).
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
            f"ระดับผู้เรียนที่เลือก: {audience}\n"
            f"ระดับความยากที่เลือก: {difficulty}\n\n"
            f"--- รายการข้อสอบ ---\n"
            f"{json.dumps(audit_payload, ensure_ascii=False, indent=2)}\n\n"
            "ส่งกลับเป็น Array JSON ของผลลัพธ์การ Audit เท่านั้น"
        )

        import requests
        try:
            logger.info(f"Agent 3 กำลังออดิทข้อสอบ {len(questions)} ข้อ สำหรับระดับ {audience}")

            url = "https://openrouter.ai/api/v1/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            dprompt = f"""
{system_prompt}

---
{user_prompt}
"""

            payload = {
                "model": self.model,
                "prompt": dprompt,
                "temperature": 0.1
            }

            print("=== PAYLOAD TO LLM (AGENT 3) ===")
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            print("================================")

            response = requests.post(url, json=payload, headers=headers, timeout=90)
            response.raise_for_status()

            resp_data = response.json()
            
            if "choices" not in resp_data or not resp_data["choices"]:
                raise Exception(f"Invalid API Response: {resp_data}")

            raw = resp_data['choices'][0]['text'].strip()

            # Clean markdown code fences if present
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0].strip()
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0].strip()

            audit_results: List[Dict] = json.loads(raw)

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

        except requests.exceptions.HTTPError as e:
            logger.error(f"Agent 3 API Error: {e.response.text}")
            for q in questions:
                q.setdefault("audit_status", "rejected")
                q.setdefault("audit_feedback", f"ถูกปฏิเสธอัตโนมัติเนื่องจากเครือข่ายขัดข้อง: HTTP {e.response.status_code}")
            return questions
        except json.JSONDecodeError as e:
            logger.error(f"Agent 3 JSON parse error: {e}")
            for q in questions:
                q.setdefault("audit_status", "rejected")
                q.setdefault("audit_feedback", "ถูกปฏิเสธอัตโนมัติเนื่องจากขั้นตอนการตรวจสอบเกิดความผิดพลาดทาง JSON")
            return questions
        except Exception as e:
            logger.error(f"Agent 3 failed: {e}")
            for q in questions:
                q.setdefault("audit_status", "rejected")
                q.setdefault("audit_feedback", f"การตรวจสอบถูกข้ามและปฏิเสธเนื่องจากระบบขัดข้อง: {str(e)}")
            return questions
