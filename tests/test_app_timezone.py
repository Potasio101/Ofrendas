from dataclasses import dataclass

from offering_app.ui.app import create_app


@dataclass
class DummySummary:
    envelopes: int
    total: float


class DummyService:
    def __init__(self):
        self.last_requested_date = None

    def get_daily_summary(self, service_date: str):
        self.last_requested_date = service_date
        return DummySummary(envelopes=0, total=0)

    def process_image(self, image_path: str):
        return {}

    def build_offering_from_form(self, form, actor):
        return {}

    def build_corrections_from_form(self, form):
        return []

    def confirm(self, offering, corrections):
        return "00000000-0000-0000-0000-000000000001"


class DummyStorage:
    def __init__(self):
        self.last_requested_date = None
        self.last_timezone = None

    def get_current_service_date(self, timezone_name: str) -> str:
        self.last_timezone = timezone_name
        return "2026-05-08"

    def get_daily_totals(self, service_date: str):
        self.last_requested_date = service_date
        return {"envelopes": 0, "total": 0}

    def get_by_date(self, service_date: str):
        self.last_requested_date = service_date
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
    app.config["APP_TIMEZONE"] = "America/Caracas"
    return app.test_client(), storage, service


def test_day_log_uses_storage_current_service_date_by_timezone():
    client, storage, _ = _build_client()

    response = client.get("/day-log", headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"})

    assert response.status_code == 200
    assert storage.last_timezone == "America/Caracas"
    assert storage.last_requested_date == "2026-05-08"


def test_summary_uses_storage_current_service_date_by_timezone():
    client, storage, service = _build_client()

    response = client.get("/summary", headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"})

    assert response.status_code == 200
    assert storage.last_timezone == "America/Caracas"
    assert service.last_requested_date == "2026-05-08"
