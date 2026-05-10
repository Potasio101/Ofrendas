import cv2
import numpy as np
from PIL import Image

from offering_app.config import FIELD_COORDS

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass


class ImageProcessor:
    @staticmethod
    def load(image_path: str) -> np.ndarray:
        img = Image.open(image_path).convert("RGB")
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    def clean(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(gray)
        denoised = cv2.fastNlMeansDenoising(contrast, h=10)
        return denoised

    def normalize_document(self, image: np.ndarray) -> np.ndarray:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 75, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return image

        image_area = image.shape[0] * image.shape[1]
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:10]:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            area = cv2.contourArea(approx)
            if len(approx) == 4 and area > image_area * 0.2:
                return self._four_point_transform(image, approx.reshape(4, 2).astype("float32"))
        return image

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

    def crop_field_variant(
        self,
        image: np.ndarray,
        field_name: str,
        offset: tuple[float, float, float, float],
    ) -> np.ndarray:
        h, w = image.shape[:2]
        x_rel, y_rel, w_rel, h_rel = FIELD_COORDS[field_name]
        dx, dy, dw, dh = offset
        x_rel = min(max(x_rel + dx, 0.0), 0.99)
        y_rel = min(max(y_rel + dy, 0.0), 0.99)
        w_rel = min(max(w_rel + dw, 0.01), 1.0 - x_rel)
        h_rel = min(max(h_rel + dh, 0.01), 1.0 - y_rel)

        x = int(w * x_rel)
        y = int(h * y_rel)
        cw = max(1, int(w * w_rel))
        ch = max(1, int(h * h_rel))
        return image[y : y + ch, x : x + cw]

    @staticmethod
    def _order_points(points: np.ndarray) -> np.ndarray:
        rect = np.zeros((4, 2), dtype="float32")
        s = points.sum(axis=1)
        rect[0] = points[np.argmin(s)]  # top-left
        rect[2] = points[np.argmax(s)]  # bottom-right

        diff = np.diff(points, axis=1)
        rect[1] = points[np.argmin(diff)]  # top-right
        rect[3] = points[np.argmax(diff)]  # bottom-left
        return rect

    def _four_point_transform(self, image: np.ndarray, points: np.ndarray) -> np.ndarray:
        rect = self._order_points(points)
        tl, tr, br, bl = rect

        width_a = np.linalg.norm(br - bl)
        width_b = np.linalg.norm(tr - tl)
        max_width = max(int(width_a), int(width_b), 1)

        height_a = np.linalg.norm(tr - br)
        height_b = np.linalg.norm(tl - bl)
        max_height = max(int(height_a), int(height_b), 1)

        dst = np.array(
            [
                [0, 0],
                [max_width - 1, 0],
                [max_width - 1, max_height - 1],
                [0, max_height - 1],
            ],
            dtype="float32",
        )
        matrix = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, matrix, (max_width, max_height))
        if warped.shape[1] < warped.shape[0]:
            warped = cv2.rotate(warped, cv2.ROTATE_90_CLOCKWISE)
        return warped
