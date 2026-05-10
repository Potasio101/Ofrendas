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


class DummyTrainingJobService:
    def __init__(self):
        self.force_calls = 0
        self.promote_calls = 0
        self.rollback_calls = 0

    def force_training(self, actor_user_id: str | None):
        self.force_calls += 1
        return {
            "enqueued": True,
            "reason": "queued",
            "job": {"id": "job-1", "status": "queued"},
            "actor_user_id": actor_user_id,
        }

    def get_status(self):
        return {
            "active_job": {"id": "job-1", "status": "running"},
            "latest_job": {"id": "job-1", "status": "running"},
            "latest_artifact": None,
            "state": "running",
        }

    def list_jobs(self, limit: int = 20):
        return [{"id": "job-1", "status": "running"}][:limit]

    def list_actions(self, limit: int = 20):
        return [{"id": "act-1", "action_type": "force"}][:limit]

    def promote_candidate(self, actor_user_id: str | None, artifact_id: str | None = None):
        self.promote_calls += 1
        if artifact_id == "blocked":
            return {
                "promoted": False,
                "reason": "gates_failed",
                "gates": {"passed": False},
            }
        return {
            "promoted": True,
            "reason": "promoted",
            "active_model": {"id": artifact_id or "artifact-1", "model_status": "active"},
            "actor_user_id": actor_user_id,
            "gates": {"passed": True},
        }

    def rollback_active_model(self, actor_user_id: str | None):
        self.rollback_calls += 1
        return {
            "rolled_back": True,
            "reason": "rolled_back",
            "active_model": {"id": "artifact-0", "model_status": "active"},
            "actor_user_id": actor_user_id,
        }


def _build_client():
    training = DummyTrainingJobService()
    app = create_app(
        service=DummyService(),
        storage=DummyStorage(),
        upload_path="/tmp",
        training_job_service=training,
    )
    app.config["TESTING"] = True
    return app.test_client(), training


def test_training_force_forbidden_for_treasurer():
    client, _ = _build_client()

    response = client.post(
        "/admin/training/force",
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
    )

    assert response.status_code == 403


def test_training_force_allowed_for_admin_and_enqueues_job():
    client, training = _build_client()

    response = client.post(
        "/admin/training/force",
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert response.status_code == 202
    assert training.force_calls == 1
    body = response.get_json()
    assert body["status"] == "ok"
    assert body["data"]["job"]["id"] == "job-1"


def test_training_status_requires_admin_role():
    client, _ = _build_client()

    denied = client.get(
        "/admin/training/status",
        headers={"X-User-Role": "auditor", "X-User-Id": "audit-user"},
    )
    allowed = client.get(
        "/admin/training/status",
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert denied.status_code == 403
    assert allowed.status_code == 200
    assert allowed.get_json()["data"]["state"] == "running"


def test_training_jobs_returns_limited_list_for_admin():
    client, _ = _build_client()

    response = client.get(
        "/admin/training/jobs?limit=1",
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["limit"] == 1
    assert len(body["data"]["items"]) == 1


def test_training_promote_requires_admin_role_and_enforces_gates():
    client, training = _build_client()

    denied = client.post(
        "/admin/training/promote",
        json={"artifact_id": "artifact-1"},
        headers={"X-User-Role": "treasurer", "X-User-Id": "treasurer-user"},
    )
    blocked = client.post(
        "/admin/training/promote",
        json={"artifact_id": "blocked"},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert denied.status_code == 403
    assert blocked.status_code == 409
    assert blocked.get_json()["data"]["reason"] == "gates_failed"
    assert training.promote_calls == 1


def test_training_promote_and_rollback_admin_actions():
    client, training = _build_client()

    promote = client.post(
        "/admin/training/promote",
        json={"artifact_id": "artifact-9"},
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )
    rollback = client.post(
        "/admin/training/rollback",
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )
    actions = client.get(
        "/admin/training/actions?limit=1",
        headers={"X-User-Role": "admin", "X-User-Id": "admin-user"},
    )

    assert promote.status_code == 200
    assert promote.get_json()["data"]["active_model"]["id"] == "artifact-9"
    assert rollback.status_code == 200
    assert rollback.get_json()["data"]["rolled_back"] is True
    assert actions.status_code == 200
    assert actions.get_json()["data"]["limit"] == 1
    assert training.promote_calls == 1
    assert training.rollback_calls == 1
