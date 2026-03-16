"""
app/services/extractors/pdf_extractor.py

Extractor implementation for PDF files using pypdf with LLM Vision OCR fallback.
- Uses pypdf for digital text extraction (fast, no API cost)
- Falls back to LLM Vision OCR for scanned/image-based pages
- Includes Tesseract as a secondary local fallback if available
"""

import logging
import asyncio
import base64
import re
import io
from pathlib import Path
from pypdf import PdfReader

from app.core.config import get_settings
from app.services.extractors.base import BaseExtractor

# OCR dependencies (optional)
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class PdfExtractor(BaseExtractor):
    """Extracts text from .pdf documents with multi-tier OCR fallback."""

    def __init__(self):
        self.settings = get_settings()
        self.ocr_model = self.settings.OPENROUTER_MODEL_OCR
        self.dpi = self.settings.OCR_DPI
        self.min_chars = self.settings.OCR_MIN_CHARS_THRESHOLD
        self.max_img_size = self.settings.OCR_MAX_IMAGE_SIZE

    # ── Text Cleaning ─────────────────────────────────────────────────────

    def _clean_text(self, text: str) -> str:
        """
        Post-processing to clean up OCR noise like redundant dashes, dots,
        and empty lines typical of form-filling templates.
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

    def _is_meaningful_text(self, text: str) -> bool:
        """
        Checks if extracted text is meaningful (not just noise/symbols).
        Returns True if the text appears to contain real content.
        """
        if not text:
            return False

        stripped = text.strip()
        if len(stripped) < self.min_chars:
            return False

        # Count actual alphanumeric characters (including Thai)
        alpha_chars = sum(1 for c in stripped if c.isalnum() or '\u0e00' <= c <= '\u0e7f')
        total_chars = len(stripped)

        if total_chars == 0:
            return False

        # If less than 30% of characters are meaningful, it's probably noise
        return (alpha_chars / total_chars) > 0.3

    # ── Image Optimization ────────────────────────────────────────────────

    def _optimize_image(self, pil_image) -> bytes:
        """
        Resizes and compresses image for efficient OCR processing.
        Returns JPEG bytes.
        """
        # Resize if too large (preserving aspect ratio)
        width, height = pil_image.size
        max_dim = self.max_img_size

        if width > max_dim or height > max_dim:
            ratio = min(max_dim / width, max_dim / height)
            new_size = (int(width * ratio), int(height * ratio))
            pil_image = pil_image.resize(new_size, Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS)
            logger.info(f"Resized image from {width}x{height} to {new_size[0]}x{new_size[1]}")

        # Convert to JPEG bytes with good quality
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format='JPEG', quality=85, optimize=True)
        return img_buffer.getvalue()

    # ── LLM Vision OCR ────────────────────────────────────────────────────

    def _extract_via_llm_vision(self, image_bytes: bytes, page_num: int) -> str:
        """Sends the page image to OpenRouter Vision API to extract text."""
        from app.core.llm import call_openrouter_vision

        prompt = (
            "คุณคือระบบ OCR ที่เชี่ยวชาญในการอ่านเอกสารภาษาไทยและอังกฤษ\n\n"
            "คำสั่ง:\n"
            "1. สกัดข้อความทั้งหมดจากภาพเอกสารนี้ให้ครบถ้วน\n"
            "2. รักษาลำดับและโครงสร้างของเนื้อหา (หัวข้อ, ย่อหน้า, รายการ)\n"
            "3. ถ้ามีตาราง ให้แปลงเป็นข้อความแบบมีโครงสร้าง\n"
            "4. ข้ามองค์ประกอบตกแต่ง เส้นคั่น หรือ placeholder เช่น '........'\n"
            "5. ห้ามสร้างเนื้อหาขึ้นใหม่ ให้สกัดเฉพาะสิ่งที่เห็นในภาพเท่านั้น\n"
            "6. ตอบเป็นข้อความล้วนๆ ไม่ต้องมี markdown หรือคำอธิบายเพิ่มเติม"
        )

        logger.info(f"Page {page_num}: Sending to Vision LLM ({self.ocr_model}), image size: {len(image_bytes)//1024}KB")

        try:
            raw = call_openrouter_vision(
                prompt=prompt,
                base64_image=base64.b64encode(image_bytes).decode('utf-8'),
                model=self.ocr_model
            )
            if raw and raw.strip():
                logger.info(f"Page {page_num}: Vision LLM returned {len(raw)} chars")
                return self._clean_text(raw)
        except Exception as e:
            logger.warning(f"Page {page_num}: Vision LLM OCR failed: {e}")

        return ""

    # ── Tesseract Local Fallback ──────────────────────────────────────────

    def _extract_via_tesseract(self, pil_image, page_num: int) -> str:
        """Uses local Tesseract OCR as a fallback. Supports Thai + English."""
        if not TESSERACT_AVAILABLE:
            return ""

        try:
            logger.info(f"Page {page_num}: Attempting Tesseract OCR (tha+eng)...")
            text = pytesseract.image_to_string(pil_image, lang='tha+eng')
            if text and text.strip():
                logger.info(f"Page {page_num}: Tesseract returned {len(text)} chars")
                return self._clean_text(text)
        except Exception as e:
            logger.warning(f"Page {page_num}: Tesseract OCR failed: {e}")

        return ""

    # ── Main Extraction Logic ─────────────────────────────────────────────

    def _extract_sync(self, path: Path) -> str:
        """Synchronous extraction with multi-tier OCR fallback."""
        reader = PdfReader(path)
        total_pages = len(reader.pages)
        text_parts = []
        ocr_pages = 0

        logger.info(f"Starting PDF extraction: {path.name} ({total_pages} pages, DPI={self.dpi})")

        for i, page in enumerate(reader.pages):
            page_num = i + 1

            # Tier 1: Direct text extraction via pypdf
            page_text = page.extract_text()

            if self._is_meaningful_text(page_text):
                text_parts.append(page_text)
                continue

            # Page needs OCR — try converting to image
            if not PDF2IMAGE_AVAILABLE:
                logger.warning(f"Page {page_num}: No text and pdf2image not available. Skipping.")
                if page_text:
                    text_parts.append(page_text)
                continue

            try:
                images = convert_from_path(
                    path,
                    first_page=page_num,
                    last_page=page_num,
                    dpi=self.dpi
                )
                if not images:
                    continue

                pil_image = images[0]
                img_bytes = self._optimize_image(pil_image)
                ocr_pages += 1

                # Tier 2: LLM Vision OCR
                ocr_text = self._extract_via_llm_vision(img_bytes, page_num)
                if self._is_meaningful_text(ocr_text):
                    text_parts.append(ocr_text)
                    continue

                # Tier 3: Tesseract local fallback
                tesseract_text = self._extract_via_tesseract(pil_image, page_num)
                if self._is_meaningful_text(tesseract_text):
                    text_parts.append(tesseract_text)
                    continue

                # Last resort: use whatever we got
                if page_text and page_text.strip():
                    text_parts.append(page_text)
                    logger.warning(f"Page {page_num}: All OCR methods returned insufficient text. Using pypdf output.")

            except Exception as e:
                logger.error(f"Page {page_num}: Image conversion failed: {e}")
                if page_text:
                    text_parts.append(page_text)

        logger.info(f"PDF extraction complete: {total_pages} pages, {ocr_pages} required OCR")
        return self._clean_text("\n\n".join(text_parts).strip())

    async def extract_text(self, file_path: Path) -> str:
        """
        Asynchronously extract text from a PDF file.
        Runs the CPU-bound extraction in the default ThreadPoolExecutor.
        """
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, self._extract_sync, file_path)
        return text
