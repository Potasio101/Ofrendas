from dataclasses import dataclass
from io import BytesIO

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

    def should_fallback_to_manual(self, data):
        return False

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

    def upsert_line(
        self,
        service_date: str,
        denomination_value: float,
        denomination_type: str,
        quantity: int,
        actor_user_id: str | None,
    ):
        return {
            "id": "cash-session-1",
            "service_date": service_date,
            "session_status": "open",
            "counted_cash_total": round(denomination_value * quantity, 2),
            "denomination_type": denomination_type,
        }

    def close_session(self, service_date: str, actor_user_id: str | None, notes: str | None):
        return {
            "id": "cash-session-1",
            "service_date": service_date,
            "session_status": "closed",
            "notes": notes,
        }

    def reopen_session(self, service_date: str, actor_user_id: str | None, reason: str | None):
        return {
            "id": "cash-session-1",
            "service_date": service_date,
            "session_status": "open",
            "notes": reason,
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

    def update_draft(self, disbursement_id: str, payload: dict, actor_user_id: str | None):
        return {
            "id": disbursement_id,
            "status": "draft",
            "description": payload.get("description") or "Updated",
        }

    def submit(self, disbursement_id: str, actor_user_id: str | None):
        return {"id": disbursement_id, "status": "submitted"}

    def approve(self, disbursement_id: str, actor_user_id: str | None):
        return {"id": disbursement_id, "status": "approved"}

    def pay(self, disbursement_id: str, actor_user_id: str | None):
        return {"id": disbursement_id, "status": "paid"}


class DummyKioskPOSService:
    def get_or_create_open_order(self, service_date: str, actor_user_id: str | None, notes: str | None):
        return {
            "id": "kiosk-order-1",
            "service_date": service_date,
            "order_status": "open",
            "subtotal": 0,
            "total": 0,
            "created": True,
            "notes": notes,
        }

    def list_items(self, active_only: bool = True):
        return [{"id": "item-1", "item_name": "Cafe", "default_price": 2.0, "is_active": True, "is_custom": False}]

    def add_catalog_line(self, kiosk_order_id: str, kiosk_item_id: str, quantity: int, actor_user_id: str | None):
        return {"id": kiosk_order_id, "order_status": "open", "subtotal": 4.0, "total": 4.0, "line_count": quantity}

    def add_custom_line(
        self,
        kiosk_order_id: str,
        item_name: str,
        unit_price: float,
        quantity: int,
        actor_user_id: str | None,
    ):
        if not item_name:
            raise ValueError("invalid_item_name")
        return {
            "id": kiosk_order_id,
            "order_status": "open",
            "subtotal": round(unit_price * quantity, 2),
            "total": round(unit_price * quantity, 2),
            "line_count": quantity,
        }

    def pay_order(
        self,
        kiosk_order_id: str,
        payment_method: str,
        amount_paid: float,
        cash_received: float | None,
        zelle_customer_name: str | None,
        transaction_reference: str | None,
        actor_user_id: str | None,
    ):
        if payment_method == "zelle" and not (zelle_customer_name or "").strip():
            raise ValueError("invalid_zelle_customer_name")
        return {
            "order": {"id": kiosk_order_id, "order_status": "paid", "total": amount_paid},
            "payment": {"payment_method": payment_method, "amount_paid": amount_paid},
        }


def _build_client():
    app = create_app(
        service=DummyService(),
        storage=DummyStorage(),
        upload_path="/tmp",
        cash_window_service=DummyCashWindowService(),
        outputs_service=DummyOutputsService(),
        kiosk_pos_service=DummyKioskPOSService(),
    )
    app.config["TESTING"] = True
    return app.test_client()


def _build_client_with(service):
    app = create_app(
        service=service,
        storage=DummyStorage(),
        upload_path="/tmp",
        cash_window_service=DummyCashWindowService(),
        outputs_service=DummyOutputsService(),
        kiosk_pos_service=DummyKioskPOSService(),
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
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["data"]["session"]["session_status"] == "open"


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
    assert response.get_json()["message"] == "Description is required"


def test_outputs_draft_created_for_admin():
    client = _build_client()

    response = client.post(
        "/outputs/draft",
        data={"description": "Desk", "amount": "10", "fund_source_code": "other"},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["data"]["disbursement"]["status"] == "draft"


def test_outputs_drafts_allowed_for_auditor():
    client = _build_client()

    response = client.get(
        "/outputs/drafts",
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert isinstance(body["data"]["items"], list)


def test_cash_window_line_forbidden_for_auditor():
    client = _build_client()

    response = client.post(
        "/cash-window/line",
        data={"service_date": "2026-05-08", "denomination_value": "20", "denomination_type": "bill", "quantity": "1"},
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 403


def test_cash_window_line_allows_treasurer():
    client = _build_client()

    response = client.post(
        "/cash-window/line",
        data={"service_date": "2026-05-08", "denomination_value": "20", "denomination_type": "bill", "quantity": "2"},
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["data"]["session"]["counted_cash_total"] == 40.0


def test_cash_window_close_allows_treasurer():
    client = _build_client()

    response = client.post(
        "/cash-window/close",
        data={"service_date": "2026-05-08", "notes": "close"},
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["data"]["session"]["session_status"] == "closed"


def test_cash_window_reopen_forbidden_for_treasurer():
    client = _build_client()

    response = client.post(
        "/cash-window/reopen",
        data={"service_date": "2026-05-08", "reason": "fix"},
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
    )

    assert response.status_code == 403


def test_cash_window_reopen_allowed_for_admin():
    client = _build_client()

    response = client.post(
        "/cash-window/reopen",
        data={"service_date": "2026-05-08", "reason": "fix"},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["data"]["session"]["session_status"] == "open"


def test_outputs_submit_forbidden_for_auditor():
    client = _build_client()

    response = client.post(
        "/outputs/disb-1/submit",
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 403


def test_outputs_submit_allows_treasurer():
    client = _build_client()

    response = client.post(
        "/outputs/disb-1/submit",
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["data"]["disbursement"]["status"] == "submitted"


def test_outputs_approve_forbidden_for_treasurer():
    client = _build_client()

    response = client.post(
        "/outputs/disb-1/approve",
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
    )

    assert response.status_code == 403


def test_outputs_approve_and_pay_allowed_for_admin():
    client = _build_client()

    approve_response = client.post(
        "/outputs/disb-1/approve",
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )
    pay_response = client.post(
        "/outputs/disb-1/pay",
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert approve_response.status_code == 200
    approve_body = approve_response.get_json()
    assert approve_body["status"] == "ok"
    assert approve_body["data"]["disbursement"]["status"] == "approved"
    assert pay_response.status_code == 200
    pay_body = pay_response.get_json()
    assert pay_body["status"] == "ok"
    assert pay_body["data"]["disbursement"]["status"] == "paid"


def test_outputs_update_draft_allows_admin():
    client = _build_client()

    response = client.post(
        "/outputs/disb-1/update",
        data={"description": "Updated description"},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["data"]["disbursement"]["status"] == "draft"


def test_kiosk_open_order_forbidden_for_auditor():
    client = _build_client()

    response = client.post(
        "/kiosk/order/open",
        data={"service_date": "2026-05-08"},
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 403


def test_kiosk_open_order_allows_admin():
    client = _build_client()

    response = client.post(
        "/kiosk/order/open",
        data={"service_date": "2026-05-08"},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["data"]["order"]["order_status"] == "open"


def test_kiosk_items_allows_auditor():
    client = _build_client()

    response = client.get(
        "/kiosk/items",
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "ok"
    assert isinstance(body["data"]["items"], list)


def test_kiosk_pay_zelle_requires_payer_name():
    client = _build_client()

    response = client.post(
        "/kiosk/order/pay",
        data={"kiosk_order_id": "kiosk-order-1", "payment_method": "zelle", "amount_paid": "10"},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert response.status_code == 400


def test_process_manual_redirects_with_manual_saved_notice():
    client = _build_client()

    response = client.post(
        "/process-manual",
        data={"member_name": "Manual Person", "diezmo": "10", "ofrenda": "5"},
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "notice=manual_saved" in response.headers["Location"]


def test_day_log_shows_manual_saved_notice():
    client = _build_client()

    response = client.get(
        "/day-log?notice=manual_saved",
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )

    assert response.status_code == 200
    assert b"Sobre manual guardado" in response.data


def test_process_shows_manual_warning_on_low_confidence_fallback():
    class FallbackService(DummyService):
        def process_image(self, image_path: str):
            return {
                "member_name": "Recognized",
                "diezmo": 0,
                "ofrenda": 0,
                "primicias": 0,
                "pro_templo": 0,
                "ofrenda_misionera": 0,
                "ofrenda_pastoral": 0,
                "payment_method": "cash",
                "ocr_confidence": 0.2,
                "image_path": image_path,
            }

        def should_fallback_to_manual(self, data):
            return True

    client = _build_client_with(FallbackService())

    response = client.post(
        "/process",
        data={"image": (BytesIO(b"fake-jpg"), "envelope.jpg")},
        content_type="multipart/form-data",
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
    )

    assert response.status_code == 200
    assert b"El OCR no pudo leer la foto con precision" in response.data
