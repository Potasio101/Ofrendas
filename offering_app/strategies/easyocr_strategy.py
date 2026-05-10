import logging
from typing import Dict, Tuple

import numpy as np

from offering_app.interfaces.i_ocr_strategy import IOCRStrategy


class EasyOCRStrategy(IOCRStrategy):
    def __init__(self) -> None:
        self._reader = None
        self._logger = logging.getLogger(__name__)

    def _load_reader(self):
        if self._reader is not None:
            return self._reader
        try:
            import easyocr

            self._reader = easyocr.Reader(["en", "es"], gpu=False)
        except ImportError as exc:
            self._logger.warning(
                "EasyOCR is not installed; OCR results will be empty until dependency is installed.",
                exc_info=exc,
            )
            self._reader = None
        except Exception as exc:
            self._logger.error("EasyOCR reader initialization failed.", exc_info=exc)
            self._reader = None
        return self._reader

    def read(self, image: np.ndarray) -> Tuple[str, float]:
        reader = self._load_reader()
        if reader is None:
            return "", 0.5
        try:
            result = reader.readtext(image)
            if not result:
                return "", 0.5
            joined = " ".join(item[1] for item in result).strip()
            avg_conf = sum(float(item[2]) for item in result) / len(result)
            return joined, round(max(avg_conf, 0.5), 4)
        except Exception as exc:
            self._logger.error("EasyOCR read failed.", exc_info=exc)
            return "", 0.5

    def read_fields(self, field_images: Dict[str, np.ndarray]) -> Dict[str, Tuple[str, float]]:
        return {field: self.read(img) for field, img in field_images.items()}
