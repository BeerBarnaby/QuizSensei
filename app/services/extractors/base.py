from abc import ABC, abstractmethod
from pathlib import Path


class BaseExtractor(ABC):
    """
    Abstract base class for all file text extractors.
    Each supported file type (e.g. .pdf, .docx, .txt) must implement this interface.
    """

    @abstractmethod
    async def extract_text(self, file_path: Path) -> str:
        """
        Reads the file at the given path and returns its extracted text.
        
        Args:
            file_path: Absolute or relative Path to the file.
            
        Returns:
            The extracted text as a string.
            
        Raises:
            Exception: If parsing fails (e.g., file is corrupted or unreadable).
        """
        pass
