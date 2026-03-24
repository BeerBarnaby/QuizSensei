"""
Agent 1 (Analyzer) - Analyzes document text for general educational topics, learner level, and content sufficiency.
"""
import json
import logging
from typing import Dict, Any

from app.core.config import Settings
from app.core.ai_base import BaseAnalyzer

logger = logging.getLogger(__name__)


class LLMDocumentAnalyzer(BaseAnalyzer):
    """
    Agent 1 – Document Analyzer
    Analyzes content, assesses target audience level, and evaluates content sufficiency.
    Outputs results in Thai for the teacher dashboard.
    """

    DEFAULT_TAXONOMY = {
        "general_education": ["core_concepts", "definitions", "applications"],
    }

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.OPENROUTER_MODEL

    def _get_system_prompt(self) -> str:
        prompt = """คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์เนื้อหาทางการศึกษาและบรรณาธิการอาวุโส (Senior Educational Content Analyst) ประจำแพลตฟอร์ม QuizSensei

ภารกิจของคุณ: วิเคราะห์เนื้อหาที่อัปโหลดเพื่อเตรียมความพร้อมสำหรับการสร้างข้อสอบที่มีคุณภาพสูง

## 1. การวิเคราะห์หมวดหมู่ (Taxonomy Classification)
ระบุกลุ่มเนื้อหาและหัวข้อย่อยที่เหมาะสมที่สุดจากเนื้อหาที่ได้รับ

## 2. การประเมินระดับภาษาและผู้เรียน (Learner Level Assessment)
วิเคราะห์ความยากของเนื้อหาและเลือกกลุ่มเป้าหมายที่เหมาะสมที่สุด (เลือก 1 จาก 5 ระดับนี้เท่านั้น):
- **ประถม**: ภาษาเรียบง่าย เน้นการสร้างนิสัยและพื้นฐานเบื้องต้น
- **มัธยมต้น**: เริ่มใช้ตรรกะและการเชื่อมโยงข้อมูล
- **มัธยมปลาย**: ความรู้เชิงทฤษฎีและหลักการสำคัญ
- **มหาวิทยาลัย**: การประยุกต์ใช้ในระดับลึกหรืองานวิจัย
- **วัยทำงาน**: การนำไปใช้ในวิชาชีพหรือการแก้ปัญหาในโลกจริง

## 3. การตรวจสอบความเพียงพอ (Content Sufficiency)
ตอบ `content_sufficiency: true` เฉพาะเมื่อเนื้อหามี "สาระสำคัญ" หรือ "ความชัดเจน" พอจะออกข้อสอบได้จริง
- **ตัวอย่างที่ไม่พอ**: เนื้อหาสั้นแค่หัวข้อ, มีแต่คำโปรยไม่มีเนื้อหาหลัก, หรือข้อความที่ไม่มีใจความสำคัญ
- **ตัวอย่างที่พอ**: มีหลักการ (Principles), วิธีการ (Methods), หรือคำอธิบายที่ชัดเจน (Explanations)

## 4. การระบุตัวชี้วัด (Learning Indicators)
สกัด "ตัวชี้วัด" หรือ "จุดประสงค์การเรียนรู้" ที่ปรากฏในเนื้อหา โดยเน้นที่ความสามารถในการนำไปใช้งานจริง (Practical Skills) หรือความเข้าใจพื้นฐานที่แน่นแฟ้น

## 5. รูปแบบการตอบกลับ (Output Format)
### ข้อปฏิบัติที่สำคัญมาก:
- ตอบกลับเป็น **JSON ภายใน Markdown Code Block (```json ... ```) เท่านั้น**
- **ห้ามมีข้อความเกริ่นนำหรือสรุปปิดท้าย**
- ใช้โครงสร้างนี้เท่านั้น:
{
  "topic": "<slug ภาษาอังกฤษ หรือหัวข้อหลัก>",
  "subtopic": "<slug ภาษาอังกฤษ หรือหัวข้อย่อย>",
  "suggested_learner_level": "<ระดับภาษาไทย>",
  "learner_level_reason": "<เหตุผลประกอบระดับผู้เรียน - สรุปให้ครูเห็นภาพใน 1 ประโยค>",
  "indicators": [
    {"id": "IND-01", "text": "ตัวชี้วัดที่ 1", "relevance": "high/medium"},
    {"id": "IND-02", "text": "ตัวชี้วัดที่ 2", "relevance": "high/medium"}
  ],
  "content_sufficiency": <true/false>,
  "sufficiency_reason": "<ชี้จุดเด่นหรือจุดที่ขาดของเนื้อหาให้ชัดเจน>",
  "should_upload_more_documents": <true/false>,
  "recommended_next_action": "<คำแนะนำสั้นๆ สำหรับครูในขั้นตอนถัดไป>",
  "status": "success",
  "message": "<สรุปภาพรวมการวิเคราะห์สั้นๆ>",
  "keywords_found": ["คำค้น 1", "คำค้น 2"]
}
"""
        return prompt

    async def analyze(self, text: str) -> Dict[str, Any]:
        """Agent 1 pipeline: classify document and evaluate sufficiency."""
        max_chars = 30_000
        truncated = text[:max_chars]

        import asyncio
        from app.core.llm import call_openrouter_json
        
        system_prompt = self._get_system_prompt()
        full_prompt = f"{system_prompt}\n\nข้อความสำหรับวิเคราะห์:\n{truncated}"
        
        parsed = await asyncio.to_thread(
            call_openrouter_json,
            prompt=full_prompt,
            model=self.model,
            temperature=0.1
        )
            
        if not parsed:
            logger.error(f"Agent 1 failed to get valid JSON response.")
            return {
                "topic": "unknown",
                "subtopic": "unknown",
                "suggested_learner_level": "ประถม",
                "content_sufficiency": False,
                "sufficiency_reason": f"API Error Fallback",
                "should_upload_more_documents": True,
                "status": "error"
            }

        parsed.setdefault("status", "success")
        parsed.setdefault("message", "Analyzed successfully")
        parsed.setdefault("analyzed_char_count", len(truncated))
        parsed.setdefault("document_id", "")
        return parsed
