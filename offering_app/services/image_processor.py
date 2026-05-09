import cv2
import numpy as np

from offering_app.config import FIELD_COORDS


class ImageProcessor:
    def clean(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(gray)
        denoised = cv2.fastNlMeansDenoising(contrast, h=10)
        return denoised

    def crop_field(self, image: np.ndarray, field_name: str) -> np.ndarray:
        h, w = image.shape[:2]
        x_rel, y_rel, w_rel, h_rel = FIELD_COORDS[field_name]
        x = int(w * x_rel)
        y = int(h * y_rel)
        cw = int(w * w_rel)
        ch = int(h * h_rel)
        return image[y : y + ch, x : x + cw]

    def crop_all_fields(self, image: np.ndarray) -> dict[str, np.ndarray]:
        return {field: self.crop_field(image, field) for field in FIELD_COORDS}
