"""
app/services/extractors/docx_extractor.py

Extractor implementation for Word documents (.docx) using python-docx.
Note: python-docx is a synchronous library, so we run the extraction in a thread pool.
"""

import asyncio
from pathlib import Path
import docx

from app.services.extractors.base import BaseExtractor


class DocxExtractor(BaseExtractor):
    """Extracts text from .docx documents."""

    def _extract_sync(self, path: Path) -> str:
        """Synchronous wrapper around python-docx logic."""
        # Note: python-docx accepts string paths or file-like objects.
        # It's safest to pass the string representation of the path.
        document = docx.Document(str(path))
        text_parts = []
        for para in document.paragraphs:
            if para.text:
                text_parts.append(para.text)
        return "\n".join(text_parts).strip()

    async def extract_text(self, file_path: Path) -> str:
        """
        Asynchronously extract text from a DOCX file.
        Runs the CPU-bound python-docx extraction in the default ThreadPoolExecutor.
        """
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, self._extract_sync, file_path)
        return text
