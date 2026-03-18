"""
Agent 1 (Analyzer) - Analyzes document text for financial literacy topics, learner level, and content sufficiency.
"""
import json
import random
import logging
from typing import Dict, Any

from app.core.config import Settings
from app.services.core.analyzers.base import BaseAnalyzer
from app.schemas.shared.agent_outputs import AnalyzerOutput

logger = logging.getLogger(__name__)


class LLMFinancialLiteracyAnalyzer(BaseAnalyzer):
    """
    Agent 1 – วิเคราะห์เอกสาร (Analyzer)
    วิเคราะห์และจัดกลุ่มเนื้อหา ประเมินระดับผู้เรียน และตรวจสอบความเพียงพอของเนื้อหา
    ผลลัพธ์ทั้งหมดอธิบายเป็นภาษาไทย
    """

    # Main Financial Literacy Taxonomy (Drafted for NECTEC/Bank of Thailand standards)
    # Maps top-level topics to specific sub-concepts used for generation and reporting.
    FL_TAXONOMY = {
        "budgeting_and_spending": ["needs_vs_wants", "fixed_vs_variable_expenses", "monthly_budgeting"],
        "saving_and_emergency_fund": ["savings_goals", "emergency_fund", "delayed_gratification"],
        "credit_and_debt": ["credit_cards", "interest_and_repayment", "good_vs_bad_debt"],
        "risk_and_insurance": ["financial_risk", "insurance_basics", "protection_planning"],
        "investment_basics": ["risk_return", "simple_investing", "diversification_basics"],
        "consumer_rights_and_financial_fraud": ["scam_awareness", "digital_finance_safety", "consumer_protection"],
    }

    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = settings.OPENROUTER_MODEL

    def _get_system_prompt(self) -> str:
        taxonomy_str = "\n".join(
            f"  {i+1}. {topic}: [{', '.join(subs)}]"
            for i, (topic, subs) in enumerate(self.FL_TAXONOMY.items())
        )
        return f"""คุณคือผู้เชี่ยวชาญด้านการวางแผนการเงินและบรรณาธิการเนื้อหาอาวุโส (Senior Financial Literacy Analyst) ประจำแพลตฟอร์ม QuizSensei

ภารกิจของคุณ: วิเคราะห์เนื้อหาที่อัปโหลด (ภาษาไทยเป็นหลัก) เพื่อเตรียมความพร้อมสำหรับการสร้างข้อสอบที่มีคุณภาพสูง

## 1. การวิเคราะห์หมวดหมู่ (Taxonomy Classification)
ระบุกลุ่มเนื้อหาที่เข้าข่ายที่สุดจากมาตรฐานการเงินพื้นฐาน:
{taxonomy_str}

## 2. การประเมินระดับภาษาและผู้เรียน (Learner Level Assessment)
วิเคราะห์ความยากของเนื้อหาและเลือกกลุ่มเป้าหมายที่เหมาะสมที่สุด:
- **ประถม**: ภาษาเรียบง่าย เน้นการสร้างนิสัย (เช่น กระปุกออมสิน, ค่าขนม)
- **มัธยมต้น**: เริ่มใช้ตรรกะเบื้องต้น (เช่น การเก็บออมเพื่อสิ่งที่อยากได้, รายรับ-รายจ่าย)
- **มัธยมปลาย**: ความรู้เชิงทฤษฎีพื้นฐาน (เช่น อัตราดอกเบี้ย, พลังของเงินฝาก, ภาษีเบื้องต้น)
- **มหาวิทยาลัย/วัยเริ่มทำงาน**: การจัดการเงินในโลกจริง (เช่น เครดิตบูโร, บัตรเครดิต, หนี้, ประกันภัย)
- **วัยทำงาน/เกษียณ**: การบริหารสินทรัพย์ขั้นสูง (เช่น การวางแผนภาษีเชิงลึก, การลงทุน, การเกษียณ)

## 3. การตรวจสอบความเพียงพอ (Content Sufficiency) **(เกณฑ์เข้มงวด)**
ตอบ `content_sufficiency: true` เฉพาะเมื่อเนื้อหามี "สาระสำคัญ" หรือ "ความชัดเจน" พอจะออกข้อสอบได้จริง
- **ตัวอย่างที่ไม่พอ**: เนื้อหาสั้นแค่หัวข้อ, มีแต่คำโปรยไม่มีนิยาม, หรือเป็นข้อความแชทที่ไม่มีความรู้
- **ตัวอย่างที่พอ**: มีหลักการ (Principles), วิธีการ (Methods), หรือเคสตัวอย่าง (Cases)

## 4. การระบุตัวชี้วัด (Learning Indicators)
สกัด "ตัวชี้วัด" หรือ "จุดประสงค์การเรียนรู้" ที่ปรากฏในเนื้อหา โดยเน้นที่ความสามารถในการนำไปใช้งานจริง (Practical Skills)
- ตัวอย่าง: "คำนวณดอกเบี้ยทบต้นได้", "จำแนกความแตกต่างระหว่างความต้องการและความจำเป็น", "เลือกประเภทประกันภัยที่เหมาะสมกับความเสี่ยง"

## 5. รูปแบบการตอบกลับ (Output Format)
กรุณาส่งกลับเป็น JSON ภายใน Markdown Code Block (```json ... ```) โดยใช้โครงสร้างนี้:
{{
  "topic": "<slug ภาษาอังกฤษ>",
  "subtopic": "<slug ภาษาอังกฤษ>",
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
}}
"""

    async def analyze(self, text: str) -> Dict[str, Any]:
        """Agent 1 pipeline: classify document and evaluate sufficiency."""
        max_chars = 30_000
        truncated = text[:max_chars]

        import asyncio
        from app.core.llm import call_openrouter_json
        
        full_prompt = f"{self._get_system_prompt()}\n\nข้อความสำหรับวิเคราะห์:\n{truncated}"
        
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

