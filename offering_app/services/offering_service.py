from datetime import date, datetime
from pathlib import Path
import re
import time
from typing import Any
from uuid import UUID, uuid4

from offering_app.interfaces.i_correction_strategy import ICorrectionStrategy
from offering_app.interfaces.i_ocr_strategy import IOCRStrategy
from offering_app.interfaces.i_storage_repo import IStorageRepo
from offering_app.interfaces.i_training_repo import ITrainingRepo
from offering_app.models.correction import Correction
from offering_app.models.offering import Offering
from offering_app.services.image_processor import ImageProcessor
from offering_app.services.ocr_debug_service import OcrDebugService


class OfferingService:
    TRAINING_FIELDS = [
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
    MEMBER_NAME_ROI_OFFSETS = [
        (0.0, 0.0, 0.0, 0.0),
        (0.0, 0.06, 0.0, 0.0),
        (0.0, 0.1, 0.0, 0.0),
        (0.02, 0.06, 0.0, 0.0),
        (-0.02, 0.06, 0.0, 0.0),
    ]
    OFRENDA_ROI_OFFSETS = [
        (0.0, 0.0, 0.0, 0.0),
        (0.03, 0.0, 0.0, 0.0),
        (-0.03, 0.0, 0.0, 0.0),
        (0.0, 0.02, 0.0, 0.0),
    ]
    NON_NAME_TERMS = {
        "bienaventurado",
        "dar",
        "dios",
        "ama",
        "hechos",
        "dador",
        "alegre",
        "recibireis",
    }
    AMOUNT_TERMS = {
        "diezmo",
        "ofrenda",
        "primicias",
        "templo",
        "misionera",
        "pastoral",
        "total",
    }

    def __init__(
        self,
        ocr: IOCRStrategy,
        corrector: ICorrectionStrategy,
        storage: IStorageRepo,
        training: ITrainingRepo,
        processor: ImageProcessor,
        members: list[str],
        ocr_debug: OcrDebugService | None = None,
    ) -> None:
        self.ocr = ocr
        self.corrector = corrector
        self.storage = storage
        self.training = training
        self.processor = processor
        self.members = members
        self.ocr_debug = ocr_debug

    def process_image(self, image_path: str) -> dict[str, Any]:
        started = time.perf_counter()
        request_id = uuid4().hex
        timings: dict[str, float] = {}

        load_started = time.perf_counter()
        image = ImageProcessor.load(image_path)
        timings["load_ms"] = round((time.perf_counter() - load_started) * 1000, 2)

        normalize_started = time.perf_counter()
        if hasattr(self.processor, "normalize_document"):
            normalized = self.processor.normalize_document(image)
        else:
            normalized = image
        timings["normalize_ms"] = round((time.perf_counter() - normalize_started) * 1000, 2)

        preprocess_started = time.perf_counter()
        cleaned = self.processor.clean(normalized)
        timings["preprocess_ms"] = round((time.perf_counter() - preprocess_started) * 1000, 2)

        crop_started = time.perf_counter()
        field_images = self.processor.crop_all_fields(cleaned)
        timings["crop_fields_ms"] = round((time.perf_counter() - crop_started) * 1000, 2)

        ocr_started = time.perf_counter()
        raw_values = self.ocr.read_fields(field_images)
        raw_values = self._refine_field_rois(cleaned, raw_values)
        timings["ocr_ms"] = round((time.perf_counter() - ocr_started) * 1000, 2)

        corrected: dict[str, Any] = {}
        confidences: list[float] = []
        correction_started = time.perf_counter()
        for field, (raw_text, raw_conf) in raw_values.items():
            value, corr_conf = self.corrector.correct(raw_text, field, self.members)
            corrected[field] = value
            corrected[f"raw_{field}"] = str(raw_text or "")
            confidences.append(min(raw_conf, corr_conf))
        timings["correction_ms"] = round((time.perf_counter() - correction_started) * 1000, 2)

        avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else 0.5
        corrected["ocr_confidence"] = avg_conf
        corrected["image_path"] = str(Path(image_path))
        corrected["ocr_request_id"] = request_id
        timings["total_ms"] = round((time.perf_counter() - started) * 1000, 2)

        if self.ocr_debug and self.ocr_debug.is_enabled():
            self.ocr_debug.write_session(
                request_id=request_id,
                input_image_path=image_path,
                preprocessed_image=cleaned,
                field_images=field_images,
                ocr_raw=raw_values,
                parsed_fields=corrected,
                timings=timings,
                meta={
                    "request_id": request_id,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "image_path": str(Path(image_path)),
                },
            )
        return corrected

    def _refine_field_rois(
        self,
        image: Any,
        raw_values: dict[str, tuple[str, float]],
    ) -> dict[str, tuple[str, float]]:
        if not hasattr(self.processor, "crop_field_variant"):
            return raw_values

        refined = dict(raw_values)
        if "member_name" in refined and self.members:
            refined["member_name"] = self._best_roi_read(
                image=image,
                field_name="member_name",
                offsets=self.MEMBER_NAME_ROI_OFFSETS,
                score=self._score_member_name_candidate,
            )
        if "ofrenda" in refined:
            refined["ofrenda"] = self._best_roi_read(
                image=image,
                field_name="ofrenda",
                offsets=self.OFRENDA_ROI_OFFSETS,
                score=self._score_amount_candidate,
            )
        return refined

    def _best_roi_read(
        self,
        image: Any,
        field_name: str,
        offsets: list[tuple[float, float, float, float]],
        score,
    ) -> tuple[str, float]:
        candidates: list[tuple[str, float]] = []
        for offset in offsets:
            roi = self.processor.crop_field_variant(image, field_name, offset)
            if roi is None or getattr(roi, "size", 0) == 0:
                continue
            candidates.append(self.ocr.read(roi))
        if not candidates:
            return "", 0.5
        return max(candidates, key=score)

    def _score_member_name_candidate(self, candidate: tuple[str, float]) -> float:
        text, confidence = candidate
        value = str(text or "").strip()
        if not value:
            return -1.0
        lowered = value.lower()
        score = float(confidence)
        if any(term in lowered for term in self.NON_NAME_TERMS):
            score -= 1.0
        if any(term in lowered for term in self.AMOUNT_TERMS):
            score -= 1.5
        if "$" in lowered:
            score -= 1.0
        alpha_chars = sum(char.isalpha() for char in value)
        score += (alpha_chars / max(len(value), 1)) * 0.2
        word_count = len(re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]+", value))
        if 1 <= word_count <= 4:
            score += 0.25
        else:
            score -= 0.2
        digit_count = sum(char.isdigit() for char in value)
        if digit_count:
            score -= min(0.4 + (digit_count / 8.0), 1.0)
        if len(value) > 40:
            score -= 0.2
        return score

    @staticmethod
    def _score_amount_candidate(candidate: tuple[str, float]) -> float:
        text, confidence = candidate
        value = str(text or "").strip()
        if not value:
            return -1.0
        digits = sum(char.isdigit() for char in value)
        letters = sum(char.isalpha() for char in value)
        score = float(confidence)
        if digits == 0:
            score -= 1.0
        else:
            score += min(digits / 6.0, 0.4)
        if letters:
            score -= min(letters / 8.0, 0.5)
        if re.search(r"\d+[.,]\d{1,2}", value):
            score += 0.25
        if len(value) <= 12:
            score += 0.1
        return score

    def should_fallback_to_manual(self, data: dict[str, Any]) -> bool:
        name = str(data.get("member_name") or "").strip().lower()
        unknown_names = {"", "miembro desconocido", "unknown", "desconocido"}
        amount_fields = [
            "diezmo",
            "ofrenda",
            "primicias",
            "pro_templo",
            "ofrenda_misionera",
            "ofrenda_pastoral",
        ]
        all_zero = all(self._to_float(data.get(field)) == 0.0 for field in amount_fields)
        low_confidence = self._to_float(data.get("ocr_confidence")) < 0.6
        return all_zero and (name in unknown_names or low_confidence)

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
        diezmo = sum(float(row.get("diezmo", 0)) for row in rows)
        ofrenda = sum(float(row.get("ofrenda", 0)) for row in rows)
        return {"envelopes": len(rows), "total": total, "diezmo": diezmo, "ofrenda": ofrenda}

    def build_offering_from_form(self, form: dict[str, str], actor_user_id: str | None) -> Offering:
        service_date_value = form.get("service_date") or date.today().isoformat()
        safe_actor_user_id = self._normalize_uuid(actor_user_id)
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
            captured_by_user_id=safe_actor_user_id,
            confirmed_by_user_id=safe_actor_user_id,
        )
        offering.compute_total()
        return offering

    @staticmethod
    def _normalize_uuid(value: str | None) -> str | None:
        if not value:
            return None
        candidate = str(value).strip()
        if not candidate:
            return None
        try:
            return str(UUID(candidate))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def build_corrections_from_form(self, form: dict[str, str]) -> list[Correction]:
        corrections: list[Correction] = []
        for field in self.TRAINING_FIELDS:
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
