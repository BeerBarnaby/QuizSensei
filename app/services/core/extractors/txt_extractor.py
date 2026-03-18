"""
Plain text extraction strategy.
Simple reader for .txt files using standard UTF-8 encoding.
"""
import aiofiles
from pathlib import Path

from app.services.core.extractors.base import BaseExtractor


class TxtExtractor(BaseExtractor):
    """Extracts text from UTF-8 encoded .txt files."""

    async def extract_text(self, file_path: Path) -> str:
        """
        Read the entire text file asynchronously.
        Assumes UTF-8 encoding.
        """
        async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
            return await f.read()
