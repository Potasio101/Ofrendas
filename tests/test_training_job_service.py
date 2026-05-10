import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from offering_app.services.training_job_service import TrainingJobService


class FakeStorage:
    def __init__(self):
        self.jobs = []
        self.artifacts = []
        self.actions = []

    def get_active_training_job(self):
        for job in reversed(self.jobs):
            if job["status"] in {"queued", "running"}:
                return dict(job)
        return None

    def create_training_job(self, trigger_type: str, requested_by_user_id: str | None):
        job = {
            "id": f"job-{len(self.jobs) + 1}",
            "trigger_type": trigger_type,
            "status": "queued",
            "requested_by_user_id": requested_by_user_id,
            "metadata": {},
        }
        self.jobs.append(job)
        return dict(job)

    def mark_training_job_running(self, job_id: str):
        for job in self.jobs:
            if job["id"] == job_id:
                job["status"] = "running"
                return dict(job)
        raise ValueError("training_job_not_found")

    def create_training_model_artifact(self, **kwargs):
        artifact = {"id": f"artifact-{len(self.artifacts) + 1}", "model_status": "candidate", **kwargs}
        self.artifacts.append(artifact)
        return dict(artifact)

    def mark_training_job_succeeded(self, job_id: str, metadata: dict):
        for job in self.jobs:
            if job["id"] == job_id:
                job["status"] = "succeeded"
                job["metadata"] = metadata
                return dict(job)
        raise ValueError("training_job_not_found")

    def mark_training_job_failed(self, job_id: str, failure_reason: str, trace_ref: str | None, metadata=None):
        for job in self.jobs:
            if job["id"] == job_id:
                job["status"] = "failed"
                job["failure_reason"] = failure_reason
                job["trace_ref"] = trace_ref
                job["metadata"] = metadata or {}
                return dict(job)
        raise ValueError("training_job_not_found")

    def mark_training_job_canceled(self, job_id: str, reason: str | None):
        for job in self.jobs:
            if job["id"] == job_id:
                job["status"] = "canceled"
                job["failure_reason"] = reason
                return dict(job)
        raise ValueError("training_job_not_found")

    def get_latest_training_job(self):
        return dict(self.jobs[-1]) if self.jobs else None

    def get_latest_training_model_artifact(self):
        return dict(self.artifacts[-1]) if self.artifacts else None

    def list_training_jobs(self, limit: int = 20):
        return [dict(item) for item in self.jobs[-limit:]][::-1]

    def get_latest_candidate_training_model_artifact(self):
        for artifact in reversed(self.artifacts):
            if artifact.get("model_status") == "candidate":
                return dict(artifact)
        return None

    def get_active_training_model_artifact(self):
        for artifact in reversed(self.artifacts):
            if artifact.get("model_status") == "active":
                return dict(artifact)
        return None

    def get_training_model_artifact(self, artifact_id: str):
        for artifact in self.artifacts:
            if artifact["id"] == artifact_id:
                return dict(artifact)
        return None

    def promote_training_model_artifact(self, artifact_id: str, actor_user_id: str | None, gate_results: dict):
        for artifact in self.artifacts:
            if artifact["id"] == artifact_id and artifact.get("model_status") == "candidate":
                for current in self.artifacts:
                    if current.get("model_status") == "active":
                        current["model_status"] = "archived"
                artifact["model_status"] = "active"
                artifact["promoted_by_user_id"] = actor_user_id
                artifact["gate_results"] = gate_results
                return dict(artifact)
        raise ValueError("training_candidate_not_found")

    def rollback_training_model(self, actor_user_id: str | None):
        active = None
        archived = None
        for artifact in self.artifacts:
            if artifact.get("model_status") == "active":
                active = artifact
            elif artifact.get("model_status") == "archived":
                archived = artifact
        if not active:
            raise ValueError("active_model_not_found")
        if not archived:
            raise ValueError("previous_model_not_found")
        active["model_status"] = "archived"
        archived["model_status"] = "active"
        archived["promoted_by_user_id"] = actor_user_id
        return dict(archived)

    def create_training_model_action(
        self,
        action_type: str,
        actor_user_id: str | None,
        artifact_id: str | None = None,
        metadata: dict | None = None,
    ):
        action = {
            "id": f"action-{len(self.actions) + 1}",
            "action_type": action_type,
            "actor_user_id": actor_user_id,
            "artifact_id": artifact_id,
            "metadata": metadata or {},
        }
        self.actions.append(action)
        return dict(action)

    def list_training_model_actions(self, limit: int = 20):
        return [dict(item) for item in self.actions[-limit:]][::-1]


def _write_sample(target: Path, field: str, ocr_read: str, corrected: str, suffix: str):
    payload = {
        "schema_version": "training_sample_v1",
        "offering_id": "11111111-1111-1111-1111-111111111111",
        "image_path": "/tmp/envelope.jpg",
        "field": field,
        "ocr_read": ocr_read,
        "corrected": corrected,
        "confidence": 0.9,
        "actor_user_id": "admin-user",
        "created_at": f"2026-05-09T12:30:0{suffix}",
        "dedupe_key": f"11111111-1111-1111-1111-111111111111:{field}:{suffix}",
    }
    target.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")


def test_force_training_runs_async_and_creates_artifact(tmp_path):
    _write_sample(tmp_path / "sample1.json", "member_name", "ANA PEREZ", "Ana Perez", "1")
    _write_sample(tmp_path / "sample2.json", "diezmo", "2S", "25", "2")

    storage = FakeStorage()
    service = TrainingJobService(storage=storage, training_path=str(tmp_path))

    result = service.force_training("admin-user")

    assert result["enqueued"] is True

    # Wait briefly for daemon thread to finish in test context.
    for _ in range(50):
        latest = storage.get_latest_training_job()
        if latest and latest["status"] in {"succeeded", "failed"}:
            break
        time.sleep(0.01)
    assert storage.get_latest_training_job()["status"] == "succeeded"
    assert storage.get_latest_training_model_artifact() is not None


def test_force_training_returns_existing_active_job(tmp_path):
    storage = FakeStorage()
    storage.jobs.append(
        {
            "id": "job-1",
            "trigger_type": "force",
            "status": "running",
            "requested_by_user_id": "admin-user",
            "metadata": {},
        }
    )
    service = TrainingJobService(storage=storage, training_path=str(tmp_path))

    result = service.force_training("admin-user")

    assert result["enqueued"] is False
    assert result["reason"] == "job_already_active"
    assert result["job"]["id"] == "job-1"


def test_scheduled_training_skips_for_low_samples(tmp_path):
    storage = FakeStorage()
    service = TrainingJobService(storage=storage, training_path=str(tmp_path), min_sample_threshold=2)

    result = service.trigger_scheduled_training()

    assert result["enqueued"] is False
    assert result["reason"] == "insufficient_samples"


def test_scheduled_training_respects_cooldown(tmp_path):
    _write_sample(tmp_path / "sample1.json", "member_name", "ANA PEREZ", "Ana Perez", "1")
    storage = FakeStorage()
    storage.jobs.append(
        {
            "id": "job-1",
            "trigger_type": "scheduled",
            "status": "succeeded",
            "requested_by_user_id": None,
            "finished_at": (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat(),
            "metadata": {},
        }
    )
    service = TrainingJobService(storage=storage, training_path=str(tmp_path), min_sample_threshold=1, cooldown_seconds=3600)

    result = service.trigger_scheduled_training()

    assert result["enqueued"] is False
    assert result["reason"] == "cooldown_active"


def test_promote_candidate_requires_passing_gates(tmp_path):
    storage = FakeStorage()
    storage.artifacts.append(
        {
            "id": "artifact-1",
            "model_status": "candidate",
            "metrics": {
                "name_match_precision": 0.9,
                "amount_parse_accuracy": 0.92,
                "fallback_reduction": 0.45,
            },
        }
    )
    service = TrainingJobService(storage=storage, training_path=str(tmp_path))

    result = service.promote_candidate(actor_user_id="admin-user", artifact_id="artifact-1")

    assert result["promoted"] is True
    assert result["active_model"]["model_status"] == "active"


def test_rollback_returns_failure_when_no_previous_model(tmp_path):
    storage = FakeStorage()
    storage.artifacts.append({"id": "artifact-a", "model_status": "active", "metrics": {}})
    service = TrainingJobService(storage=storage, training_path=str(tmp_path))

    result = service.rollback_active_model(actor_user_id="admin-user")

    assert result["rolled_back"] is False
    assert result["reason"] == "previous_model_not_found"
