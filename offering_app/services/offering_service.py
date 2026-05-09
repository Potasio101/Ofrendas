from datetime import date, datetime
from pathlib import Path
from typing import Any

import cv2

from offering_app.interfaces.i_correction_strategy import ICorrectionStrategy
from offering_app.interfaces.i_ocr_strategy import IOCRStrategy
from offering_app.interfaces.i_storage_repo import IStorageRepo
from offering_app.interfaces.i_training_repo import ITrainingRepo
from offering_app.models.correction import Correction
from offering_app.models.offering import Offering
from offering_app.services.image_processor import ImageProcessor


class OfferingService:
    def __init__(
        self,
        ocr: IOCRStrategy,
        corrector: ICorrectionStrategy,
        storage: IStorageRepo,
        training: ITrainingRepo,
        processor: ImageProcessor,
        members: list[str],
    ) -> None:
        self.ocr = ocr
        self.corrector = corrector
        self.storage = storage
        self.training = training
        self.processor = processor
        self.members = members

    def process_image(self, image_path: str) -> dict[str, Any]:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Invalid image file")

        cleaned = self.processor.clean(image)
        field_images = self.processor.crop_all_fields(cleaned)
        raw_values = self.ocr.read_fields(field_images)

        corrected: dict[str, Any] = {}
        confidences: list[float] = []
        for field, (raw_text, raw_conf) in raw_values.items():
            value, corr_conf = self.corrector.correct(raw_text, field, self.members)
            corrected[field] = value
            confidences.append(min(raw_conf, corr_conf))

        avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else 0.5
        corrected["ocr_confidence"] = avg_conf
        corrected["image_path"] = str(Path(image_path))
        return corrected

    def confirm(
        self,
        offering: Offering,
        corrections: list[Correction],
    ) -> str:
        offering_id = self.storage.save(offering)
        for correction in corrections:
            correction.offering_id = offering_id
            self.training.save_correction(correction)
        return offering_id

    def get_daily_summary(self, service_date: str) -> dict[str, Any]:
        if hasattr(self.storage, "get_daily_totals"):
            return self.storage.get_daily_totals(service_date)

        rows = self.storage.get_by_date(service_date)
        total = sum(float(row.get("total", 0)) for row in rows)
        return {"envelopes": len(rows), "total": total}

    def build_offering_from_form(self, form: dict[str, str], actor_user_id: str | None) -> Offering:
        service_date_value = form.get("service_date") or date.today().isoformat()
        offering = Offering(
            member_name=form.get("member_name", ""),
            diezmo=float(form.get("diezmo", 0) or 0),
            ofrenda=float(form.get("ofrenda", 0) or 0),
            primicias=float(form.get("primicias", 0) or 0),
            pro_templo=float(form.get("pro_templo", 0) or 0),
            ofrenda_misionera=float(form.get("ofrenda_misionera", 0) or 0),
            ofrenda_pastoral=float(form.get("ofrenda_pastoral", 0) or 0),
            service_date=date.fromisoformat(service_date_value),
            payment_method=form.get("payment_method", "cash"),
            image_path=form.get("image_path"),
            ocr_confidence=float(form.get("ocr_confidence", 0.5) or 0.5),
            captured_by_user_id=actor_user_id,
            confirmed_by_user_id=actor_user_id,
        )
        offering.compute_total()
        return offering

    def build_corrections_from_form(self, form: dict[str, str]) -> list[Correction]:
        fields = [
            "member_name",
            "diezmo",
            "ofrenda",
            "primicias",
            "pro_templo",
            "ofrenda_misionera",
            "ofrenda_pastoral",
            "service_date",
            "payment_method",
        ]
        corrections: list[Correction] = []
        for field in fields:
            value = form.get(field, "")
            corrections.append(
                Correction(
                    image_path=form.get("image_path", ""),
                    field=field,
                    ocr_read=form.get(f"raw_{field}", ""),
                    corrected=value,
                    confidence=float(form.get("ocr_confidence", 0.5) or 0.5),
                    created_at=datetime.utcnow(),
                )
            )
        return corrections
