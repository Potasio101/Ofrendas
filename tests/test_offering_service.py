import numpy as np

from offering_app.services.offering_service import OfferingService
from offering_app.services.ocr_debug_service import OcrDebugService


class DummyStorage:
    def get_daily_totals(self, service_date: str):
        return {"envelopes": 2, "total": 55.5}


class DummyTraining:
    def save_correction(self, correction):
        return True


class CapturingTraining:
    def __init__(self):
        self.saved = []

    def save_correction(self, correction):
        self.saved.append(correction)
        return True


class SavingStorage:
    def save(self, offering):
        return "11111111-1111-1111-1111-111111111111"


class DummyOCR:
    def read(self, image):
        return "", 0.5

    def read_fields(self, field_images):
        return {}


class PopulatedOCR:
    def read_fields(self, field_images):
        return {
            "member_name": ("Ana Perez", 0.91),
            "diezmo": ("25", 0.88),
            "payment_method": ("cash", 0.93),
        }


class DummyCorrector:
    def correct(self, text, field, members):
        return text, 0.5


class DummyProcessor:
    def clean(self, image):
        return image

    def crop_all_fields(self, image):
        return {}


class ProcessorWithRois(DummyProcessor):
    def clean(self, image):
        return np.zeros((80, 120), dtype=np.uint8)

    def crop_all_fields(self, image):
        return {
            "member_name": np.zeros((10, 40), dtype=np.uint8),
            "diezmo": np.zeros((10, 20), dtype=np.uint8),
            "ofrenda": np.zeros((10, 20), dtype=np.uint8),
        }


def test_get_daily_summary_uses_storage_totals_when_available():
    service = OfferingService(
        ocr=DummyOCR(),
        corrector=DummyCorrector(),
        storage=DummyStorage(),
        training=DummyTraining(),
        processor=DummyProcessor(),
        members=[],
    )

    summary = service.get_daily_summary("2026-05-08")

    assert summary["envelopes"] == 2
    assert summary["total"] == 55.5


def test_build_offering_from_form_normalizes_invalid_actor_user_id_to_none():
    service = OfferingService(
        ocr=DummyOCR(),
        corrector=DummyCorrector(),
        storage=DummyStorage(),
        training=DummyTraining(),
        processor=DummyProcessor(),
        members=[],
    )

    offering = service.build_offering_from_form(
        {
            "member_name": "Test",
            "diezmo": "1",
            "ofrenda": "1",
            "service_date": "2026-05-08",
            "payment_method": "cash",
        },
        actor_user_id="not-a-uuid",
    )

    assert offering.captured_by_user_id is None
    assert offering.confirmed_by_user_id is None


def test_should_fallback_to_manual_when_low_confidence_and_zero_amounts():
    service = OfferingService(
        ocr=DummyOCR(),
        corrector=DummyCorrector(),
        storage=DummyStorage(),
        training=DummyTraining(),
        processor=DummyProcessor(),
        members=[],
    )

    should_fallback = service.should_fallback_to_manual(
        {
            "member_name": "Persona valida",
            "diezmo": "0",
            "ofrenda": "0",
            "primicias": "0",
            "pro_templo": "0",
            "ofrenda_misionera": "0",
            "ofrenda_pastoral": "0",
            "ocr_confidence": "0.4",
        }
    )

    assert should_fallback is True


def test_process_image_includes_raw_ocr_fields_in_payload(monkeypatch):
    monkeypatch.setattr("offering_app.services.image_processor.ImageProcessor.load", staticmethod(lambda *_: object()))
    service = OfferingService(
        ocr=PopulatedOCR(),
        corrector=DummyCorrector(),
        storage=DummyStorage(),
        training=DummyTraining(),
        processor=DummyProcessor(),
        members=[],
    )

    result = service.process_image("/tmp/envelope.jpg")

    assert result["raw_member_name"] == "Ana Perez"
    assert result["raw_diezmo"] == "25"
    assert result["raw_payment_method"] == "cash"
    assert result["ocr_confidence"] > 0


def test_build_corrections_from_form_uses_raw_values():
    service = OfferingService(
        ocr=DummyOCR(),
        corrector=DummyCorrector(),
        storage=DummyStorage(),
        training=DummyTraining(),
        processor=DummyProcessor(),
        members=[],
    )

    corrections = service.build_corrections_from_form(
        {
            "image_path": "/tmp/envelope.jpg",
            "ocr_confidence": "0.87",
            "member_name": "Ana",
            "raw_member_name": "ANA PEREZ",
            "diezmo": "25",
            "raw_diezmo": "2S",
            "payment_method": "cash",
            "raw_payment_method": "ca5h",
        }
    )

    member = next(item for item in corrections if item.field == "member_name")
    diezmo = next(item for item in corrections if item.field == "diezmo")
    payment = next(item for item in corrections if item.field == "payment_method")

    assert member.ocr_read == "ANA PEREZ"
    assert diezmo.ocr_read == "2S"
    assert payment.ocr_read == "ca5h"


def test_confirm_sets_offering_id_on_saved_corrections():
    training = CapturingTraining()
    service = OfferingService(
        ocr=DummyOCR(),
        corrector=DummyCorrector(),
        storage=SavingStorage(),
        training=training,
        processor=DummyProcessor(),
        members=[],
    )

    offering = service.build_offering_from_form(
        {
            "member_name": "Test",
            "service_date": "2026-05-08",
            "payment_method": "cash",
        },
        actor_user_id=None,
    )
    corrections = service.build_corrections_from_form(
        {
            "image_path": "/tmp/envelope.jpg",
            "member_name": "Test",
            "raw_member_name": "TE5T",
            "service_date": "2026-05-08",
            "payment_method": "cash",
        }
    )

    offering_id = service.confirm(offering, corrections)

    assert offering_id == "11111111-1111-1111-1111-111111111111"
    assert training.saved
    assert all(item.offering_id == offering_id for item in training.saved)


def test_process_image_creates_debug_artifacts_when_enabled(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "offering_app.services.image_processor.ImageProcessor.load",
        staticmethod(lambda *_: np.zeros((80, 120, 3), dtype=np.uint8)),
    )
    debug_dir = tmp_path / "ocr-debug"
    image_path = tmp_path / "envelope.jpg"
    image_path.write_bytes(b"fake-image")
    service = OfferingService(
        ocr=PopulatedOCR(),
        corrector=DummyCorrector(),
        storage=DummyStorage(),
        training=DummyTraining(),
        processor=ProcessorWithRois(),
        members=[],
        ocr_debug=OcrDebugService(
            base_path=str(debug_dir),
            enabled=True,
            retention_days=7,
            max_sessions=500,
        ),
    )

    result = service.process_image(str(image_path))

    session_path = debug_dir / result["ocr_request_id"]
    assert session_path.exists()
    assert (session_path / "input.jpg").exists()
    assert (session_path / "preprocessed.jpg").exists()
    assert (session_path / "name_roi.jpg").exists()
    assert (session_path / "diezmo_roi.jpg").exists()
    assert (session_path / "ofrenda_roi.jpg").exists()
    assert (session_path / "ocr_raw.json").exists()
    assert (session_path / "parsed_fields.json").exists()
    assert (session_path / "timings.json").exists()
    assert (session_path / "meta.json").exists()


def test_process_image_skips_debug_artifacts_when_disabled(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "offering_app.services.image_processor.ImageProcessor.load",
        staticmethod(lambda *_: np.zeros((80, 120, 3), dtype=np.uint8)),
    )
    debug_dir = tmp_path / "ocr-debug"
    image_path = tmp_path / "envelope.jpg"
    image_path.write_bytes(b"fake-image")
    service = OfferingService(
        ocr=PopulatedOCR(),
        corrector=DummyCorrector(),
        storage=DummyStorage(),
        training=DummyTraining(),
        processor=ProcessorWithRois(),
        members=[],
        ocr_debug=OcrDebugService(
            base_path=str(debug_dir),
            enabled=False,
            retention_days=7,
            max_sessions=500,
        ),
    )

    service.process_image(str(image_path))

    assert list(debug_dir.iterdir()) == []


def test_process_image_tolerates_debug_write_failures(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(
        "offering_app.services.image_processor.ImageProcessor.load",
        staticmethod(lambda *_: np.zeros((80, 120, 3), dtype=np.uint8)),
    )
    def _raise_disk_full(*_):
        raise OSError("disk full")

    monkeypatch.setattr("offering_app.services.ocr_debug_service.shutil.copy2", _raise_disk_full)
    debug_dir = tmp_path / "ocr-debug"
    image_path = tmp_path / "envelope.jpg"
    image_path.write_bytes(b"fake-image")
    service = OfferingService(
        ocr=PopulatedOCR(),
        corrector=DummyCorrector(),
        storage=DummyStorage(),
        training=DummyTraining(),
        processor=ProcessorWithRois(),
        members=[],
        ocr_debug=OcrDebugService(
            base_path=str(debug_dir),
            enabled=True,
            retention_days=7,
            max_sessions=500,
        ),
    )

    caplog.set_level("ERROR")
    result = service.process_image(str(image_path))

    assert result["member_name"] == "Ana Perez"
    assert any("ocr_debug_write_failed" in rec.getMessage() for rec in caplog.records)
