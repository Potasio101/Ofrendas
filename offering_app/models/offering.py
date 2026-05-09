from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Offering:
    member_name: str
    diezmo: float = 0.0
    ofrenda: float = 0.0
    primicias: float = 0.0
    pro_templo: float = 0.0
    ofrenda_misionera: float = 0.0
    ofrenda_pastoral: float = 0.0
    service_date: Optional[date] = None
    payment_method: str = "cash"
    total: float = 0.0
    image_path: Optional[str] = None
    ocr_confidence: Optional[float] = None
    captured_by_user_id: Optional[str] = None
    confirmed_by_user_id: Optional[str] = None

    def compute_total(self) -> float:
        self.total = round(
            self.diezmo
            + self.ofrenda
            + self.primicias
            + self.pro_templo
            + self.ofrenda_misionera
            + self.ofrenda_pastoral,
            2,
        )
        return self.total
