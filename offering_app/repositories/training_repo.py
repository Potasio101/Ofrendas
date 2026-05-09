import json
from dataclasses import asdict
from pathlib import Path

from offering_app.interfaces.i_training_repo import ITrainingRepo
from offering_app.models.correction import Correction


class TrainingRepo(ITrainingRepo):
    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_correction(self, correction: Correction) -> bool:
        day_dir = self.base_path / correction.created_at.strftime("%Y-%m-%d")
        day_dir.mkdir(parents=True, exist_ok=True)
        target = day_dir / f"{correction.field}_{int(correction.created_at.timestamp())}.json"
        target.write_text(json.dumps(asdict(correction), default=str, ensure_ascii=True), encoding="utf-8")
        return True
