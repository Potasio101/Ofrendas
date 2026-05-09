from dataclasses import dataclass

from offering_app.ui.app import create_app


@dataclass
class DummySummary:
    envelopes: int
    total: float


class DummyService:
    def get_daily_summary(self, service_date: str):
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
    def get_current_service_date(self, timezone_name: str) -> str:
        return "2026-05-08"

    def get_daily_totals(self, service_date: str):
        return {"envelopes": 0, "total": 0}

    def get_by_date(self, service_date: str):
        return []

    def get_offering(self, offering_id: str):
        return None

    def update_offering_fields(self, offering_id: str, updates: dict[str, str], changed_by_user_id, reason):
        return False


def _build_client(auth_mode: str):
    app = create_app(service=DummyService(), storage=DummyStorage(), upload_path="/tmp")
    app.config["TESTING"] = True
    app.config["APP_AUTH_MODE"] = auth_mode
    return app.test_client()


def test_header_strict_denies_missing_identity_headers():
    client = _build_client("header-strict")

    response = client.get("/day-log")

    assert response.status_code == 401


def test_header_strict_allows_with_valid_identity_headers():
    client = _build_client("header-strict")

    response = client.get(
        "/day-log",
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 200


def test_header_strict_denies_invalid_role_header():
    client = _build_client("header-strict")

    response = client.get(
        "/day-log",
        headers={"X-User-Role": "guest", "X-User-Id": "guest-user"},
    )

    assert response.status_code == 401
