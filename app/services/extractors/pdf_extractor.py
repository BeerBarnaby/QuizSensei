"""
app/services/extractors/pdf_extractor.py

Extractor implementation for PDF files using pypdf.
Note: pypdf is a synchronous library, so we run the extraction in a thread pool
to avoid blocking the FastAPI event loop.
"""

import asyncio
from pathlib import Path
from pypdf import PdfReader

from app.services.extractors.base import BaseExtractor


class PdfExtractor(BaseExtractor):
    """Extracts text from .pdf documents."""

    def _extract_sync(self, path: Path) -> str:
        """Synchronous wrapper around pypdf logic."""
        reader = PdfReader(path)
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
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
