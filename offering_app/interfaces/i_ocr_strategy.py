from abc import ABC, abstractmethod
from typing import Dict, Tuple

import numpy as np


class IOCRStrategy(ABC):
    @abstractmethod
    def read(self, image: np.ndarray) -> Tuple[str, float]:
        """Read text from a field image and return text and confidence."""

    @abstractmethod
    def read_fields(self, field_images: Dict[str, np.ndarray]) -> Dict[str, Tuple[str, float]]:
        """Read all field images and return values per field."""
