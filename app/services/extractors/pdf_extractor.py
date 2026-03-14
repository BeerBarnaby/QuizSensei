"""
app/services/extractors/pdf_extractor.py

Extractor implementation for PDF files using pypdf.
Note: pypdf is a synchronous library, so we run the extraction in a thread pool
to avoid blocking the FastAPI event loop.
"""

import logging
import asyncio
import base64
import json
import io
import random
from pathlib import Path
from pypdf import PdfReader
import requests

from app.core.config import get_settings

# OCR dependencies
try:
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from app.services.extractors.base import BaseExtractor

logger = logging.getLogger(__name__)

class PdfExtractor(BaseExtractor):
    """Extracts text from .pdf documents."""

    def __init__(self):
        self.settings = get_settings()
        keys = self.settings.openrouter_keys_list
        self.api_key = random.choice(keys) if keys else "dummy"
        self.model = "openai/gpt-oss-120b:free" # Use the user requested model for OCR

    def _extract_via_llm_vision(self, image_bytes: bytes) -> str:
        """Sends the page image to OpenRouter Vision API to extract text."""
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        url = "https://openrouter.ai/api/v1/responses"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Extract all the text from this image exactly as it appears. Do not add any formatting, comments, or your own words. Just output the pure extracted text."
                        },
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
        
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        
        resp_data = response.json()
        raw = ""
        if "output" in resp_data and len(resp_data["output"]) > 0:
            first_output = resp_data["output"][0]
            if "content" in first_output and len(first_output["content"]) > 0:
                 raw = first_output["content"][0].get("text", "").strip()
        
        return raw

    def _extract_sync(self, path: Path) -> str:
        """Synchronous wrapper around pypdf logic with OCR fallback."""
        reader = PdfReader(path)
        text_parts = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            
            # If standard extraction gets reasonable text, use it
            if page_text and len(page_text.strip()) > 50:
                text_parts.append(page_text)
            else:
                # Fallback to OCR for this specific page if it appears to be a scanned image
                if OCR_AVAILABLE:
                    try:
                        logger.info(f"Page {i+1} has no selectable text. Attempting Vision LLM OCR...")
                        # Convert only this page (1-indexed for pdf2image)
                        images = convert_from_path(path, first_page=i+1, last_page=i+1)
                        if images:
                            # Save PIL image to bytes
                            img_byte_arr = io.BytesIO()
                            images[0].save(img_byte_arr, format='JPEG')
                            img_bytes = img_byte_arr.getvalue()
                            
                            ocr_text = self._extract_via_llm_vision(img_bytes)
                            if ocr_text and ocr_text.strip():
                                text_parts.append(ocr_text)
                    except Exception as e:
                        logger.warning(f"Vision LLM OCR failed on page {i+1} of {path.name}: {e}")
                else:
                    if page_text:
                        text_parts.append(page_text)

        return "\n\n".join(text_parts).strip()

    async def extract_text(self, file_path: Path) -> str:
        """
        Asynchronously extract text from a PDF file.
        Runs the CPU-bound pypdf extraction in the default ThreadPoolExecutor.
        """
        loop = asyncio.get_running_loop()
        # run_in_executor(None, ...) uses the default ThreadPool
        text = await loop.run_in_executor(None, self._extract_sync, file_path)
        return text
