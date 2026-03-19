"""
PDF text extraction strategy.
Uses pypdf for digital text extraction. OCR has been removed.
"""
import logging
import asyncio
import re
from pathlib import Path
from pypdf import PdfReader

from app.core.config import get_settings
from app.services.core.extractors.base import BaseExtractor

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
        Extract text from PDF using Digital Extraction (pypdf).
        """
        raw_text = ""
        try:
            def _read_digital():
                reader = PdfReader(file_path)
                digital_pages = []
                for page in reader.pages:
                    text = page.extract_text() or ""
                    digital_pages.append(text)
                return "\n\n".join(digital_pages).strip()

            raw_text = await asyncio.to_thread(_read_digital)
            return self._clean_text(raw_text)

        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {e}")
            return raw_text
