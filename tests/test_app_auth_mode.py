from dataclasses import dataclass
import hashlib
import hmac
import time

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
    app.config["APP_AUTH_PROXY_TOKEN"] = "proxy-secret"
    app.config["APP_AUTH_PROXY_SIGNING_SECRET"] = "proxy-secret"
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


def test_proxy_token_denies_missing_token_header():
    client = _build_client("proxy-token")

    response = client.get(
        "/day-log",
        headers={"X-Auth-Role": "auditor", "X-Auth-User-Id": "audit-user"},
    )

    assert response.status_code == 401


def test_proxy_token_denies_invalid_token_header():
    client = _build_client("proxy-token")

    response = client.get(
        "/day-log",
        headers={
            "X-Auth-Proxy-Token": "wrong-token",
            "X-Auth-Role": "auditor",
            "X-Auth-User-Id": "audit-user",
        },
    )

    assert response.status_code == 401


def test_proxy_token_allows_valid_token_and_identity():
    client = _build_client("proxy-token")

    response = client.get(
        "/day-log",
        headers={
            "X-Auth-Proxy-Token": "proxy-secret",
            "X-Auth-Role": "auditor",
            "X-Auth-User-Id": "audit-user",
        },
    )

    assert response.status_code == 200


def _signed_headers(role: str, user_id: str, ts: int, secret: str):
    payload = f"{role}:{user_id}:{ts}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return {
        "X-Auth-Role": role,
        "X-Auth-User-Id": user_id,
        "X-Auth-Timestamp": str(ts),
        "X-Auth-Signature": signature,
    }


def test_proxy_signed_denies_missing_signature_headers():
    client = _build_client("proxy-signed")

    response = client.get(
        "/day-log",
        headers={"X-Auth-Role": "auditor", "X-Auth-User-Id": "audit-user"},
    )

    assert response.status_code == 401


def test_proxy_signed_denies_stale_timestamp():
    client = _build_client("proxy-signed")
    stale_ts = int(time.time()) - 1000
    headers = _signed_headers("auditor", "audit-user", stale_ts, "proxy-secret")

    response = client.get("/day-log", headers=headers)

    assert response.status_code == 401


def test_proxy_signed_denies_invalid_signature():
    client = _build_client("proxy-signed")
    now_ts = int(time.time())
    headers = {
        "X-Auth-Role": "auditor",
        "X-Auth-User-Id": "audit-user",
        "X-Auth-Timestamp": str(now_ts),
        "X-Auth-Signature": "bad-signature",
    }

    response = client.get("/day-log", headers=headers)

    assert response.status_code == 401


def test_proxy_signed_allows_valid_signature():
    client = _build_client("proxy-signed")
    now_ts = int(time.time())
    headers = _signed_headers("auditor", "audit-user", now_ts, "proxy-secret")

    response = client.get("/day-log", headers=headers)

    assert response.status_code == 200
