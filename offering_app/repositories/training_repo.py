import json
from pathlib import Path

from offering_app.interfaces.i_training_repo import ITrainingRepo
from offering_app.models.correction import Correction


class TrainingRepo(ITrainingRepo):
    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_correction(self, correction: Correction) -> bool:
        sample = self._to_training_sample(correction)
        day_dir = self.base_path / correction.created_at.strftime("%Y-%m-%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        target = day_dir / f"{sample['field']}_{int(correction.created_at.timestamp())}.json"
        target.write_text(json.dumps(sample, ensure_ascii=True), encoding="utf-8")
        return True

    @staticmethod
    def _to_training_sample(correction: Correction) -> dict:
        image_path = str(correction.image_path or "").strip()
        field = str(correction.field or "").strip()
        corrected = str(correction.corrected or "").strip()
        offering_id = str(correction.offering_id or "").strip()
        created_at = correction.created_at.isoformat()

        required_values = {
            "image_path": image_path,
            "field": field,
            "corrected": corrected,
            "offering_id": offering_id,
            "created_at": created_at,
        }
        missing = [key for key, value in required_values.items() if not value]
        if missing:
            missing_csv = ",".join(missing)
            raise ValueError(f"invalid_training_sample:{missing_csv}")

        dedupe_key = f"{offering_id}:{field}:{created_at}"
        return {
            "schema_version": "training_sample_v1",
            "offering_id": offering_id,
            "image_path": image_path,
            "field": field,
            "ocr_read": str(correction.ocr_read or ""),
            "corrected": corrected,
            "confidence": float(correction.confidence),
            "actor_user_id": str(correction.corrected_by_user_id or "").strip(),
            "created_at": created_at,
            "dedupe_key": dedupe_key,
        }
