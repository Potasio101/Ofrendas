from offering_app.services.offering_service import OfferingService


class DummyStorage:
    def get_daily_totals(self, service_date: str):
        return {"envelopes": 2, "total": 55.5}


class DummyTraining:
    def save_correction(self, correction):
        return True


class DummyOCR:
    def read(self, image):
        return "", 0.5

    def read_fields(self, field_images):
        return {}


class DummyCorrector:
    def correct(self, text, field, members):
        return text, 0.5


class DummyProcessor:
    def clean(self, image):
        return image

    def crop_all_fields(self, image):
        return {}


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
