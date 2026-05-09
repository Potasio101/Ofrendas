from abc import ABC, abstractmethod
from typing import Tuple


class ICorrectionStrategy(ABC):
    @abstractmethod
    def correct(self, text: str, field: str, members: list[str]) -> Tuple[str, float]:
        """Correct OCR text for a specific field and return corrected value and confidence."""
