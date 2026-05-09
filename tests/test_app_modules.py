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


class DummyCashWindowService:
    def __init__(self):
        self.open_calls = 0

    def open_session(self, service_date: str, actor_user_id: str | None, notes: str | None):
        self.open_calls += 1
        return {
            "id": "cash-session-1",
            "service_date": service_date,
            "session_status": "open",
            "created": True,
            "notes": notes,
            "actor_user_id": actor_user_id,
        }

    def get_session(self, service_date: str):
        return {
            "id": "cash-session-1",
            "service_date": service_date,
            "session_status": "open",
        }


class DummyOutputsService:
    def __init__(self):
        self.create_calls = 0

    def create_draft(self, payload: dict, actor_user_id: str | None):
        self.create_calls += 1
        return {
            "id": "disb-1",
            "status": "draft",
            "description": payload["description"],
            "amount": float(payload["amount"]),
            "fund_source_code": payload["fund_source_code"],
            "actor_user_id": actor_user_id,
        }

    def list_drafts(self, output_date: str | None):
        return [{"id": "disb-1", "status": "draft", "output_date": output_date or "2026-05-08"}]


def _build_client():
    app = create_app(
        service=DummyService(),
        storage=DummyStorage(),
        upload_path="/tmp",
        cash_window_service=DummyCashWindowService(),
        outputs_service=DummyOutputsService(),
    )
    app.config["TESTING"] = True
    return app.test_client()


def test_cash_window_open_forbidden_for_auditor():
    client = _build_client()

    response = client.post(
        "/cash-window/open",
        data={"service_date": "2026-05-08", "notes": "n"},
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 403


def test_cash_window_open_allows_treasurer():
    client = _build_client()

    response = client.post(
        "/cash-window/open",
        data={"service_date": "2026-05-08", "notes": "n"},
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
    )

    assert response.status_code == 201
    assert response.get_json()["session_status"] == "open"


def test_outputs_draft_forbidden_for_auditor():
    client = _build_client()

    response = client.post(
        "/outputs/draft",
        data={"description": "Desk", "amount": "10"},
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 403


def test_outputs_draft_requires_description():
    client = _build_client()

    response = client.post(
        "/outputs/draft",
        data={"amount": "10"},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert response.status_code == 400


def test_outputs_draft_created_for_admin():
    client = _build_client()

    response = client.post(
        "/outputs/draft",
        data={"description": "Desk", "amount": "10", "fund_source_code": "other"},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert response.status_code == 201
    assert response.get_json()["status"] == "draft"


def test_outputs_drafts_allowed_for_auditor():
    client = _build_client()

    response = client.get(
        "/outputs/drafts",
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 200
    assert isinstance(response.get_json()["items"], list)
