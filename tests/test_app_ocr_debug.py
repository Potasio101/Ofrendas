from dataclasses import dataclass

from offering_app.ui.app import create_app


@dataclass
class DummySummary:
    envelopes: int
    total: float


class DummyService:
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

    def should_fallback_to_manual(self, data):
        return False

    def build_offering_from_form(self, form, actor):
        return {"actor": actor}

    def build_corrections_from_form(self, form):
        return []

    def confirm(self, offering, corrections):
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


class DummyDebugService:
    def __init__(self):
        self.enabled = False
        self.sessions = [
            {"request_id": "req-1", "created_at": "2026-05-10T00:00:00Z", "files": ["meta.json"]},
        ]

    def get_status(self):
        return {
            "enabled": self.enabled,
            "retention_days": 7,
            "max_sessions": 500,
            "base_path": "/app/data/ocr-debug",
        }

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        return self.get_status()

    def list_sessions(self, limit: int = 20):
        return self.sessions[:limit]

    def get_session(self, request_id: str):
        if request_id != "req-1":
            return None
        return {
            "request_id": "req-1",
            "files": ["meta.json"],
            "meta": {"request_id": "req-1"},
            "timings": {"total_ms": 1},
            "ocr_raw": {"member_name": {"text": "Test", "confidence": 0.9}},
            "parsed_fields": {"member_name": "Test"},
        }


def _build_client():
    app = create_app(
        service=DummyService(),
        storage=DummyStorage(),
        upload_path="/tmp",
        ocr_debug_service=DummyDebugService(),
    )
    app.config["TESTING"] = True
    return app.test_client()


def test_admin_dashboard_shows_ocr_debug_block_for_admin():
    client = _build_client()

    response = client.get("/admin", headers={"X-User-Role": "admin", "X-User-Id": "admin-user"})

    assert response.status_code == 200
    assert b"OCR Debug" in response.data


def test_admin_ocr_debug_status_forbidden_for_non_admin():
    client = _build_client()

    response = client.get("/admin/ocr-debug/status", headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"})

    assert response.status_code == 403


def test_admin_ocr_debug_toggle_transitions_status():
    client = _build_client()

    response_on = client.post(
        "/admin/ocr-debug/toggle",
        json={"enabled": True},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )
    response_off = client.post(
        "/admin/ocr-debug/toggle",
        json={"enabled": False},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert response_on.status_code == 200
    assert response_on.get_json()["data"]["enabled"] is True
    assert response_off.status_code == 200
    assert response_off.get_json()["data"]["enabled"] is False


def test_admin_ocr_debug_session_endpoints_require_admin():
    client = _build_client()

    sessions_response = client.get("/admin/ocr-debug/sessions", headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"})
    session_response = client.get("/admin/ocr-debug/session/req-1", headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"})

    assert sessions_response.status_code == 403
    assert session_response.status_code == 403
