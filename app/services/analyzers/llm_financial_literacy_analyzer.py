"""
app/services/analyzers/llm_financial_literacy_analyzer.py

Agent 1: Analyzer
Classifies the document by FL topic/subtopic, Target Learner Level, and evaluates Content Sufficiency for question generation.
All output must be strictly in Thai.
"""

"""
Financial Literacy analyzer powered by LLM (Agent 1).
Performs semantic analysis to identify topics, subtopics, and content sufficiency.
"""
import json
import random
import logging
from typing import Dict, Any
import httpx

from app.core.config import Settings
from app.services.analyzers.base import BaseAnalyzer
from app.schemas.agent_outputs import AnalyzerOutput

logger = logging.getLogger(__name__)


class LLMFinancialLiteracyAnalyzer(BaseAnalyzer):
    """
    Agent 1 – วิเคราะห์เอกสาร (Analyzer)
    วิเคราะห์และจัดกลุ่มเนื้อหา ประเมินระดับผู้เรียน และตรวจสอบความเพียงพอของเนื้อหา
    ผลลัพธ์ทั้งหมดอธิบายเป็นภาษาไทย
    """

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
        return f"""คุณคือ Agent 1 (Analyzer) ของแพลตฟอร์ม QuizSensei

หน้าที่ของคุณคือวิเคราะห์อัปโหลดเนื้อหาเอกสาร (ภาษาไทย 100%) แล้วตอบกลับเป็นโครงสร้าง JSON ทันที

## กฎ 1: หมวดหมู่ (Taxonomy)
พิจารณาเนื้อหาว่าเข้าข่ายหมวดหมู่ใดที่สุดจากลิสต์นี้:
{taxonomy_str}

## กฎ 2: ระดับผู้เรียน (Learner Level)
เลือกระดับของเนื้อหา 1 ระดับจาก {{"ประถม", "มัธยมต้น", "มัธยมปลาย", "มหาวิทยาลัย", "วัยทำงาน"}}
- ประถม: ศัพท์ง่ายๆ กิจวัตรประจำวัน กระปุกออมสิน
- มัธยมต้น: ค่าขนม การออมเบื้องต้น
- มัธยมปลาย: เริ่มมีคอนเซปต์ซับซ้อนขึ้น แผนการใช้เงิน อัตราดอกเบี้ยพื้นฐาน
- มหาวิทยาลัย: เครดิต การลงทุนพื้นฐาน แนวคิดที่เฉพาะทางยิ่งขึ้น
- วัยทำงาน: ภาษี ประกันสังคม การเกษียณ เงินเฟ้อ โครงสร้างหนี้

## กฎ 3: ความเพียงพอของเนื้อหา (Content Sufficiency) **(สำคัญมาก)**
เอกสารนี้มี "เนื้อหาเพียงพอ" ที่จะนำไปตั้งคำถามเจาะลึก 3-5 ข้อไหม?
- ถ้าสั้นเกินไป (เช่นมีประโยคเดียว หรือแค่หัวข้อเนื้อหาเปล่าๆ) -> content_sufficiency: false
- ขาดความรู้หรือคำนิยามหรือหลักการปฏิบัติที่ชัดเจน (เช่นเป็นแค่แชทพูดคุยทั่วไป) -> content_sufficiency: false
- ไม่เกี่ยวกับการเงินการลงทุนจริงๆ เลย -> content_sufficiency: false
- มีข้อมูลเพียงพอ มีนิยาม หลักการ หรือตัวอย่างเชิงลึก -> content_sufficiency: true

## กฎ 4: รูปแบบ JSON Output ที่บังคับใช้
กรุณาส่งกลับแค่ JSON ที่ตรงกับรูปแบบล่างนี้เท่านั้น ห้ามใช้ Markdown code fences ถ้าข้อมูลไหนไม่ระบุให้เป็นสตริงว่างหรือ None

{{
  "topic": "<topic ภาษาอังกฤษตาม Taxonomy ด้านบน>",
  "subtopic": "<subtopic ภาษาอังกฤษตาม Taxonomy ด้านบน>",
  "suggested_learner_level": "<1 ใน 5 ระดับภาษาไทย>",
  "learner_level_reason": "<คำอธิบายภาษาไทยชี้แจงเหตุผลว่าทำไมถึงเลือกระดับนี้ 1-2 ประโยค>",
  "content_sufficiency": <true / false>,
  "sufficiency_reason": "<คำอธิบายภาษาไทย ระบุว่าเนื้อหานี้ลึกหรือยาวพอจะออกข้อสอบหรือไม่>",
  "should_upload_more_documents": <true ถ้า sufficiency เป็น false, ไม่เช่นนั้นให้ false>,
  "recommended_next_action": "<คำแนะนำสั้นๆ ภาษาไทย เช่น 'เริ่มสร้างแบบทดสอบได้เลย' หรือ 'กรุณาอัปโหลดเอกสารที่มีเนื้อหาเชิงลึกเพิ่มเติม'>",
  "status": "success",
  "message": "<ข้อความแสดงสถานะแจ้งผู้ใช้ ภาษาไทย เช่น 'วิเคราะห์เนื้อหาสำเร็จและพร้อมใช้งาน' หรือ 'เนื้อหาไม่เพียงพอ'>",
  "keywords_found": ["<คำสำคัญในบทความ 1>", "<คำสำคัญ 2>"]
}}
"""

    async def analyze(self, text: str) -> Dict[str, Any]:
        """Agent 1 pipeline: classify document and evaluate sufficiency."""
        max_chars = 30_000
        truncated = text[:max_chars]

        from app.core.llm import call_openrouter_json
        
        full_prompt = f"{self._get_system_prompt()}\n\nข้อความสำหรับวิเคราะห์:\n{truncated}"
        
        parsed = call_openrouter_json(
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

