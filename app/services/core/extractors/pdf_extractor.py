"""
PDF text extraction strategy.
Uses pdf2image and vision-based OCR (via LLM) as a primary extraction method for complex layouts.
"""
import logging
import io
import asyncio
from pathlib import Path
from pypdf import PdfReader
from pdf2image import convert_from_path

from app.core.config import get_settings
from app.services.core.extractors.base import BaseExtractor
from app.services.core.ocr_service import ocr_service

logger = logging.getLogger(__name__)

class PDFExtractor(BaseExtractor):
    """Extracts text from .pdf documents using direct text extraction."""

    def __init__(self):
        self.settings = get_settings()

    def _clean_text(self, text: str) -> str:
        """
        Post-processing to clean up extraction noise.
        """
        if not text:
            return ""

        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip lines that are just symbols (dashes/dots/underscores)
            if re.match(r'^[\s\-\._=…]{5,}$', stripped):
                continue
            # Collapse long runs of symbols within valid lines
            line = re.sub(r'[\-\._=…]{5,}', ' ', line)
            cleaned_lines.append(line.rstrip())

        text = '\n'.join(cleaned_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    async def extract_text(self, file_path: Path) -> str:
        """
        Extract text from PDF using 3-tier approach:
        1. Digital (pypdf)
        2. Vision LLM (via Image Conversion)
        3. Tesseract (Fallback)
        """
        raw_text = ""
        try:
            # ── TIER 1: Digital Extraction ────────────────────────────────────
            def _read_digital():
                reader = PdfReader(file_path)
                digital_pages = []
                for page in reader.pages:
                    text = page.extract_text() or ""
                    digital_pages.append(text)
                return "\n\n".join(digital_pages).strip()

            raw_text = await asyncio.to_thread(_read_digital)
            
            # Check if digital extraction is sufficient
            if len(raw_text) >= self.settings.OCR_MIN_TEXT_LENGTH:
                logger.info(f"Digital extraction successful for {file_path} ({len(raw_text)} chars)")
                return await ocr_service.refine_content(raw_text)
            
            logger.warning(f"Digital text too short ({len(raw_text)} chars). Triggering OCR for {file_path}")

            # ── TIER 2 & 3: OCR on Images ─────────────────────────────────────
            # If digital extraction failed or was too short, we fall back to OCR.
            # Step A: Convert PDF pages to high-quality images.
            images = await asyncio.to_thread(convert_from_path, file_path)
            ocr_pages = []
            
            for i, image in enumerate(images):
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='JPEG')
                image_bytes = img_byte_arr.getvalue()
                
                logger.info(f"Processing OCR for page {i+1} of {file_path}")
                
                # Step B: Tier 2 - Try Vision LLM (Preferred for complex layouts/Thai)
                page_text = await ocr_service.extract_from_image_vision(image_bytes)
                
                # Step C: Tier 3 - Fallback to Tesseract (Deterministic/Local)
                if not page_text:
                    logger.warning(f"Vision OCR failed for page {i+1}, using Tesseract")
                    page_text = await ocr_service.extract_from_image(image_bytes)
                
                if page_text:
                    ocr_pages.append(page_text)

            ocr_full_text = "\n\n".join(ocr_pages).strip()
            
            # Step D: Final refinement to fix OCR noise
            if ocr_full_text:
                return await ocr_service.refine_content(ocr_full_text)
            
            return raw_text # Return whatever we found if OCR also failed

        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {e}")
            return raw_text
