from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Correction:
    image_path: str
    field: str
    ocr_read: str
    corrected: str
    confidence: float
    created_at: datetime
    offering_id: Optional[str] = None
    corrected_by_user_id: Optional[str] = None
