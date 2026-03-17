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

from app.core.config import get_settings
from app.core.llm import call_openrouter_json, call_openrouter_text

settings = get_settings()
logger = logging.getLogger(__name__)

# Configure pytesseract
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

class OCRService:
    @staticmethod
    async def extract_from_image(image_bytes: bytes, lang: str = "tha+eng") -> str:
        """Perform local OCR using Tesseract on an image."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            # Optimization: Convert to grayscale for better OCR
            image = image.convert('L')
            text = pytesseract.image_to_string(image, lang=lang)
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
            # We use httpx directly here as call_openrouter_text might not support multi-modal payload yet
            # or we can adapt call_openrouter_text later.
            keys = settings.openrouter_keys_list
            if not keys:
                raise ValueError("No API keys configured.")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {keys[0]}",
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
            "You are a professional editor. Below is raw text extracted from a document via OCR. "
            "It might contain artifacts, misspellings, or broken formatting. "
            "Please clean it up, fix Thai/English spelling, and format it into clean Markdown. "
            "Preserve all factual information. Keep the language same as source. "
            "Output ONLY the cleaned Markdown content.\n\n"
            f"--- RAW TEXT ---\n{raw_text}\n--- END RAW TEXT ---"
        )

        try:
            refined = await call_openrouter_text(prompt, system_prompt="You are an expert document processor.")
            return refined.strip()
        except Exception as e:
            logger.warning(f"Content refinement failed: {e}. Returning raw text.")
            return raw_text

ocr_service = OCRService()
