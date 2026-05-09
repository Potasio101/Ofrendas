from dataclasses import dataclass

from offering_app.ui.app import create_app


@dataclass
class DummySummary:
    envelopes: int
    total: float


class DummyService:
    def get_daily_summary(self, service_date: str):
        return DummySummary(envelopes=1, total=50)

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
        return {"envelopes": 1, "total": 50}

    def get_by_date(self, service_date: str):
        return []

    def get_offering(self, offering_id: str):
        return None

    def update_offering_fields(self, offering_id: str, updates: dict[str, str], changed_by_user_id, reason):
        return False


class DummyCashWindowService:
    def open_session(self, service_date: str, actor_user_id: str | None, notes: str | None):
        return {"id": "cash-1", "session_status": "open", "created": True, "service_date": service_date}

    def get_session(self, service_date: str):
        return {"id": "cash-1", "session_status": "open", "service_date": service_date}

    def upsert_line(self, service_date: str, denomination_value: float, denomination_type: str, quantity: int, actor_user_id: str | None):
        return {"id": "cash-1", "session_status": "open", "service_date": service_date}

    def close_session(self, service_date: str, actor_user_id: str | None, notes: str | None):
        return {"id": "cash-1", "session_status": "closed", "service_date": service_date}

    def reopen_session(self, service_date: str, actor_user_id: str | None, reason: str | None):
        return {"id": "cash-1", "session_status": "open", "service_date": service_date}


class DummyOutputsService:
    def create_draft(self, payload: dict, actor_user_id: str | None):
        return {"id": "disb-1", "status": "draft", "description": payload["description"]}

    def list_drafts(self, output_date: str | None):
        return []

    def update_draft(self, disbursement_id: str, payload: dict, actor_user_id: str | None):
        return {"id": disbursement_id, "status": "draft"}

    def submit(self, disbursement_id: str, actor_user_id: str | None):
        return {"id": disbursement_id, "status": "submitted"}

    def approve(self, disbursement_id: str, actor_user_id: str | None):
        return {"id": disbursement_id, "status": "approved"}

    def pay(self, disbursement_id: str, actor_user_id: str | None):
        return {"id": disbursement_id, "status": "paid"}


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


def test_workflow_cash_view_renders_for_auditor():
    client = _build_client()

    response = client.get("/workflow/cash", headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"})

    assert response.status_code == 200
    assert b"Cash Workflow" in response.data


def test_workflow_outputs_view_renders_for_auditor():
    client = _build_client()

    response = client.get("/workflow/outputs", headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"})

    assert response.status_code == 200
    assert b"Outputs Workflow" in response.data
