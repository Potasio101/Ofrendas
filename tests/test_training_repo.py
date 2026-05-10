import json
from datetime import datetime

import pytest

from offering_app.models.correction import Correction
from offering_app.repositories.training_repo import TrainingRepo


def test_save_correction_writes_training_sample_v1(tmp_path):
    repo = TrainingRepo(str(tmp_path))
    correction = Correction(
        image_path="/tmp/envelope.jpg",
        field="member_name",
        ocr_read="ANA PEREZ",
        corrected="Ana Perez",
        confidence=0.91,
        created_at=datetime(2026, 5, 9, 12, 30, 0),
        offering_id="11111111-1111-1111-1111-111111111111",
        corrected_by_user_id="22222222-2222-2222-2222-222222222222",
    )

    saved = repo.save_correction(correction)

    assert saved is True
    files = list(tmp_path.rglob("*.json"))
    assert len(files) == 1
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    assert payload["schema_version"] == "training_sample_v1"
    assert payload["ocr_read"] == "ANA PEREZ"
    assert payload["actor_user_id"] == "22222222-2222-2222-2222-222222222222"
    assert payload["dedupe_key"] == "11111111-1111-1111-1111-111111111111:member_name:2026-05-09T12:30:00"


def test_save_correction_rejects_incomplete_sample(tmp_path):
    repo = TrainingRepo(str(tmp_path))
    correction = Correction(
        image_path="",
        field="member_name",
        ocr_read="ANA",
        corrected="Ana",
        confidence=0.8,
        created_at=datetime(2026, 5, 9, 12, 30, 0),
        offering_id="",
        corrected_by_user_id="admin-user",
    )

    with pytest.raises(ValueError, match="invalid_training_sample"):
        repo.save_correction(correction)
