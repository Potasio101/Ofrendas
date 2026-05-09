from dataclasses import dataclass

from offering_app.ui.app import create_app


@dataclass
class DummySummary:
    envelopes: int
    total: float


class DummyService:
    def __init__(self):
        self.confirm_calls = 0

    def get_daily_summary(self, service_date: str):
        return DummySummary(envelopes=1, total=10.0)

    def process_image(self, image_path: str):
        return {
            "member_name": "Test",
            "diezmo": 1,
            "ofrenda": 1,
            "primicias": 0,
            "pro_templo": 0,
            "ofrenda_misionera": 0,
            "ofrenda_pastoral": 0,
            "payment_method": "cash",
            "ocr_confidence": 0.9,
            "image_path": image_path,
        }

    def build_offering_from_form(self, form, actor):
        return {"actor": actor}

    def build_corrections_from_form(self, form):
        return []

    def confirm(self, offering, corrections):
        self.confirm_calls += 1
        return "00000000-0000-0000-0000-000000000001"


class DummyStorage:
    def get_daily_totals(self, service_date: str):
        return {"envelopes": 1, "total": 10}

    def get_by_date(self, service_date: str):
        return []

    def get_offering(self, offering_id: str):
        return None

    def update_offering_fields(self, offering_id: str, updates: dict[str, str], changed_by_user_id, reason):
        return False


def _build_client():
    service = DummyService()
    storage = DummyStorage()
    app = create_app(service=service, storage=storage, upload_path="/tmp")
    app.config["TESTING"] = True
    return app.test_client(), service


def test_confirm_forbidden_for_auditor_role():
    client, service = _build_client()

    response = client.post(
        "/confirm",
        data={"member_name": "A", "service_date": "2026-05-08"},
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 403
    assert service.confirm_calls == 0


def test_confirm_allowed_for_treasurer_role():
    client, service = _build_client()

    response = client.post(
        "/confirm",
        data={
            "member_name": "A",
            "diezmo": "1",
            "ofrenda": "1",
            "primicias": "0",
            "pro_templo": "0",
            "ofrenda_misionera": "0",
            "ofrenda_pastoral": "0",
            "service_date": "2026-05-08",
            "payment_method": "cash",
        },
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
    )

    assert response.status_code == 302
    assert service.confirm_calls == 1


def test_day_log_allowed_for_auditor_role():
    client, _ = _build_client()

    response = client.get("/day-log", headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"})

    assert response.status_code == 200
