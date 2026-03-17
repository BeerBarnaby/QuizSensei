"""
Image extractor for QuizSensei.
Uses OCRService to extract text from JPG, PNG, WEBP files.
"""
from typing import Optional
from app.services.extractors.base import BaseExtractor
from app.services.ocr_service import ocr_service
import logging

logger = logging.getLogger(__name__)

class ImageExtractor(BaseExtractor):
    async def extract_text(self, file_path: str) -> str:
        """Extract text from an image file using tiered OCR."""
        try:
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            
            logger.info(f"Starting OCR for image: {file_path}")
            
            # Tier 1: Vision LLM (Preferred for images due to complex layout)
            text = await ocr_service.extract_from_image_vision(image_bytes)
            
            # Tier 2: Tesseract Fallback
            if not text:
                logger.warning(f"Vision OCR empty for {file_path}, falling back to Tesseract.")
                text = await ocr_service.extract_from_image(image_bytes)
            
            # Final step: Content Refinement via LLM
            if text:
                logger.info(f"Refining extracted text for {file_path}")
                text = await ocr_service.refine_content(text)
                
            return text or ""
        except Exception as e:
            logger.error(f"Image extraction failed for {file_path}: {e}")
            return ""
