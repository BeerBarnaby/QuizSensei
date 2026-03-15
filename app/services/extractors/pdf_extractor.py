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
        self.model = self.settings.OPENROUTER_MODEL
        self.ocr_model = self.settings.OPENROUTER_MODEL_OCR

    def _clean_text(self, text: str) -> str:
        """
        Post-processing to clean up OCR noise like redundant dashes, dots,
        and empty lines typical of form-filling templates.
        """
        import re
        if not text:
            return ""
            
        # Remove lines that are just dashes, dots, or underscores (common in forms)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # If line is mostly symbols (more than 5 continuous dashes/dots/underscores)
            if re.match(r'^[\s\-\._=…]{5,}$', stripped):
                continue
            # Remove trailing/leading symbols from valid lines
            line = re.sub(r'[\-\._=…]{5,}', ' ', line)
            cleaned_lines.append(line.rstrip())
            
        # Join and collapse multiple newlines
        text = '\n'.join(cleaned_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _extract_via_llm_vision(self, image_bytes: bytes) -> str:
        """Sends the page image to OpenRouter Vision API to extract text."""
        from app.core.llm import call_openrouter_vision
        
        prompt = (
            "Extract all meaningful Thai and English text from this document image. "
            "Ignore background decorative elements, lines, or placeholders (like '........'). "
            "Format the output into clean, readable paragraphs. "
            "If there are tables, represent them as structured text. "
            "Output ONLY the extracted text."
        )
        
        logger.info(f"Targeting OCR Model: {self.ocr_model}")
        raw = call_openrouter_vision(
            prompt=prompt,
            base64_image=base64.b64encode(image_bytes).decode('utf-8'),
            model=self.ocr_model
        )
        
        return self._clean_text(raw or "")

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

        return self._clean_text("\n\n".join(text_parts).strip())

    async def extract_text(self, file_path: Path) -> str:
        """
        Asynchronously extract text from a PDF file.
        Runs the CPU-bound pypdf extraction in the default ThreadPoolExecutor.
        """
        loop = asyncio.get_running_loop()
        # run_in_executor(None, ...) uses the default ThreadPool
        text = await loop.run_in_executor(None, self._extract_sync, file_path)
        return text
