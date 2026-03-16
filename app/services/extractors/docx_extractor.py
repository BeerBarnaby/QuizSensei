"""
DOCX text extraction strategy.
Uses python-docx to parse and extract structured text from Microsoft Word documents.
"""
import asyncio
import io
import base64
import logging
from pathlib import Path
import docx

from app.core.config import get_settings
from app.services.extractors.base import BaseExtractor

# OCR dependencies (optional)
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocxExtractor(BaseExtractor):
    """Extracts text from .docx documents, including embedded images via OCR."""

    def __init__(self):
        self.settings = get_settings()

    def _optimize_image(self, pil_image) -> bytes:
        """Resizes and compresses image for OCR processing."""
        max_dim = self.settings.OCR_MAX_IMAGE_SIZE
        width, height = pil_image.size

        if width > max_dim or height > max_dim:
            ratio = min(max_dim / width, max_dim / height)
            new_size = (int(width * ratio), int(height * ratio))
            pil_image = pil_image.resize(new_size, Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS)

        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format='JPEG', quality=85, optimize=True)
        return img_buffer.getvalue()

    def _ocr_image_via_vision(self, image_bytes: bytes, img_index: int) -> str:
        """Sends an embedded image to LLM Vision API for OCR."""
        from app.core.llm import call_openrouter_vision

        prompt = (
            "สกัดข้อความทั้งหมดจากภาพนี้ให้ครบถ้วน ทั้งภาษาไทยและอังกฤษ\n"
            "รักษาโครงสร้างของเนื้อหา ถ้ามีตารางให้แปลงเป็นข้อความ\n"
            "ห้ามสร้างเนื้อหาขึ้นใหม่ สกัดเฉพาะสิ่งที่เห็นในภาพ\n"
            "ตอบเป็นข้อความล้วนๆ"
        )

        try:
            raw = call_openrouter_vision(
                prompt=prompt,
                base64_image=base64.b64encode(image_bytes).decode('utf-8'),
                model=self.settings.OPENROUTER_MODEL_OCR
            )
            if raw and raw.strip():
                logger.info(f"Image {img_index}: Vision LLM returned {len(raw)} chars")
                return raw.strip()
        except Exception as e:
            logger.warning(f"Image {img_index}: Vision LLM OCR failed: {e}")

        return ""

    def _ocr_image_via_tesseract(self, pil_image, img_index: int) -> str:
        """Uses local Tesseract OCR as fallback for images."""
        if not TESSERACT_AVAILABLE:
            return ""
        try:
            text = pytesseract.image_to_string(pil_image, lang='tha+eng')
            if text and text.strip():
                logger.info(f"Image {img_index}: Tesseract returned {len(text)} chars")
                return text.strip()
        except Exception as e:
            logger.warning(f"Image {img_index}: Tesseract OCR failed: {e}")
        return ""

    def _extract_embedded_images(self, document) -> list:
        """Extracts image data from inline shapes in the DOCX."""
        images = []
        try:
            for i, rel in enumerate(document.part.rels.values()):
                if "image" in rel.reltype:
                    try:
                        image_data = rel.target_part.blob
                        if len(image_data) > 1024:  # Skip tiny images (icons/bullets)
                            images.append((i, image_data))
                    except Exception as e:
                        logger.warning(f"Could not read embedded image {i}: {e}")
        except Exception as e:
            logger.warning(f"Could not scan for embedded images: {e}")
        return images

    def _extract_sync(self, path: Path) -> str:
        """Synchronous wrapper around python-docx logic with image OCR."""
        document = docx.Document(str(path))

        # 1. Extract paragraph text
        text_parts = []
        for para in document.paragraphs:
            if para.text:
                text_parts.append(para.text)

        paragraph_text = "\n".join(text_parts).strip()

        # 2. Extract and OCR embedded images
        embedded_images = self._extract_embedded_images(document)
        if embedded_images:
            logger.info(f"Found {len(embedded_images)} embedded images in {path.name}")

            image_texts = []
            for img_index, img_data in embedded_images:
                try:
                    pil_image = Image.open(io.BytesIO(img_data)).convert("RGB")
                    img_bytes = self._optimize_image(pil_image)

                    # Try LLM Vision first
                    ocr_text = self._ocr_image_via_vision(img_bytes, img_index)
                    if not ocr_text:
                        # Fallback to Tesseract
                        ocr_text = self._ocr_image_via_tesseract(pil_image, img_index)

                    if ocr_text:
                        image_texts.append(ocr_text)
                except Exception as e:
                    logger.warning(f"Failed to process embedded image {img_index}: {e}")

            if image_texts:
                combined_image_text = "\n\n".join(image_texts)
                if paragraph_text:
                    return paragraph_text + "\n\n--- เนื้อหาจากรูปภาพ ---\n\n" + combined_image_text
                return combined_image_text

        return paragraph_text

    async def extract_text(self, file_path: Path) -> str:
        """
        Asynchronously extract text from a DOCX file.
        Runs the CPU-bound python-docx extraction in the default ThreadPoolExecutor.
        """
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, self._extract_sync, file_path)
        return text
