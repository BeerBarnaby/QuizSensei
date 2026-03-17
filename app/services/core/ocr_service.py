"""
Unified OCR Service for QuizSensei.
Handles 3-tier extraction: Digital (already in extractors), Vision LLM, and Tesseract.
Also includes LLM-based content refinement.
"""
import base64
import logging
import pytesseract
from PIL import Image
from pathlib import Path
from typing import Optional, List
import io
import httpx
import asyncio

from app.core.config import get_settings
from app.core.llm import call_openrouter_json, call_openrouter_text, get_llm_api_key

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure pytesseract
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

class OCRService:
    @staticmethod
    async def extract_from_image(image_bytes: bytes, lang: str = "tha+eng") -> str:
        """Perform local OCR using Tesseract on an image."""
        try:
            def _ocr():
                image = Image.open(io.BytesIO(image_bytes))
                # Optimization: Convert to grayscale for better OCR
                image = image.convert('L')
                return pytesseract.image_to_string(image, lang=lang)
            
            text = await asyncio.to_thread(_ocr)
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract OCR failed: {e}")
            return ""

    @staticmethod
    async def extract_from_image_vision(image_bytes: bytes, prompt: Optional[str] = None) -> str:
        """Perform Vision LLM OCR using OpenRouter."""
        if not prompt:
            prompt = (
                "Extract all text from this document image. "
                "Maintain the structure (headers, lists, tables) using Markdown. "
                "If there is Thai text, extract it accurately. "
                "Do not add any commentary, just return the text content."
            )

        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Prepare the multi-modal payload for OpenRouter
        # This includes both the text instructions and the base64-encoded image
        payload = {
            "model": settings.VISION_LLM_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        }

        try:
            api_key = get_llm_api_key()
            if api_key == "dummy":
                raise ValueError("No API keys configured.")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "https://quizsensei.ai", # Required by some models
                        "X-Title": "QuizSensei"
                    },
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            logger.error(f"Vision LLM OCR failed: {e}")
            return ""

    @staticmethod
    async def refine_content(raw_text: str) -> str:
        """Use LLM to clean up and structure raw OCR text into proper Markdown."""
        if not raw_text or len(raw_text) < 10:
            return raw_text

        prompt = (
            "คุณคือบรรณาธิการเอกสารมืออาชีพ (Expert Document Editor)\n\n"
            "เนื้อหาด้านล่างนี้ได้มาจากการทำ OCR ซึ่งอาจมีตัวอักษรผิดเพี้ยน, สระจม, หรือจัดโครงสร้างผิดพลาด\n\n"
            "ภารกิจของคุณ:\n"
            "1. ปรับปรุงไวยากรณ์ไทยให้สละสลวย อ่านง่าย และลื่นไหล (Natural Thai Flow)\n"
            "2. แก้คำสะกดผิดที่เกิดจากความผิดพลาดของ OCR ทั้งภาษาไทยและภาษาอังกฤษ\n"
            "3. รักษาโครงสร้างเดิม (หัวข้อ, ลิสต์, ลำดับ) โดยใช้ Markdown\n"
            "4. ห้ามเปลี่ยนแปลงเนื้อหาเชิงข้อเท็จจริงหรือตัวเลขใดๆ ทั้งสิ้น\n"
            "5. ห้ามแสดงความคิดเห็นเพิ่มเติม ให้ส่งกลับเฉพาะเนื้อหาที่ปรับปรุงแล้วเท่านั้น\n\n"
            f"--- RAW OCR TEXT ---\n{raw_text}\n--- END ---"
        )

        try:
            # call_openrouter_text is a synchronous blocking call.
            # We use asyncio.to_thread to run it in a separate thread, 
            # preventing it from blocking the main FastAPI event loop.
            loop = asyncio.get_running_loop()
            refined = await loop.run_in_executor(None, lambda: call_openrouter_text(prompt))
            return refined.strip() if refined else raw_text
        except Exception as e:
            logger.warning(f"Content refinement failed: {e}. Returning raw text.")
            return raw_text

ocr_service = OCRService()
