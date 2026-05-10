import hashlib
import json
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class NoopTrainingJobService:
    def __init__(self) -> None:
        self.promotion_thresholds = {
            "name_match_precision": 0.85,
            "amount_parse_accuracy": 0.9,
            "fallback_reduction": 0.2,
        }

    def force_training(self, actor_user_id: str | None) -> dict[str, Any]:
        return {
            "enqueued": False,
            "reason": "training_unavailable",
            "job": None,
            "actor_user_id": actor_user_id,
        }

    def trigger_scheduled_training(self) -> dict[str, Any]:
        return {
            "enqueued": False,
            "reason": "training_unavailable",
            "job": None,
            "actor_user_id": None,
        }

    def get_status(self) -> dict[str, Any]:
        return {
            "active_job": None,
            "latest_job": None,
            "latest_artifact": None,
            "active_model": None,
            "candidate_model": None,
            "promotion_thresholds": dict(self.promotion_thresholds),
            "state": "idle",
        }

    def list_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        _ = limit
        return []

    def list_actions(self, limit: int = 20) -> list[dict[str, Any]]:
        _ = limit
        return []

    def promote_candidate(self, actor_user_id: str | None, artifact_id: str | None = None) -> dict[str, Any]:
        _ = artifact_id
        return {
            "promoted": False,
            "reason": "training_unavailable",
            "candidate": None,
            "active_model": None,
            "gates": {
                "passed": False,
                "thresholds": dict(self.promotion_thresholds),
                "checks": {},
            },
            "actor_user_id": actor_user_id,
        }

    def rollback_active_model(self, actor_user_id: str | None) -> dict[str, Any]:
        return {
            "rolled_back": False,
            "reason": "training_unavailable",
            "active_model": None,
            "actor_user_id": actor_user_id,
        }


class TrainingJobService:
    def __init__(
        self,
        storage,
        training_path: str,
        app_logger=None,
        min_sample_threshold: int = 10,
        cooldown_seconds: int = 60 * 60,
        promotion_thresholds: dict[str, float] | None = None,
    ) -> None:
        self.storage = storage
        self.training_path = Path(training_path)
        self.training_path.mkdir(parents=True, exist_ok=True)
        self.models_path = self.training_path / "models"
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.app_logger = app_logger
        self._lock = threading.Lock()
        self.min_sample_threshold = max(1, int(min_sample_threshold))
        self.cooldown_seconds = max(0, int(cooldown_seconds))
        self.promotion_thresholds = {
            "name_match_precision": 0.85,
            "amount_parse_accuracy": 0.9,
            "fallback_reduction": 0.2,
        }
        if promotion_thresholds:
            for key in self.promotion_thresholds:
                if key in promotion_thresholds:
                    self.promotion_thresholds[key] = float(promotion_thresholds[key])

    def force_training(self, actor_user_id: str | None) -> dict[str, Any]:
        return self._enqueue_training(trigger_type="force", actor_user_id=actor_user_id)

    def trigger_scheduled_training(self) -> dict[str, Any]:
        return self._enqueue_training(trigger_type="scheduled", actor_user_id=None)

    def _enqueue_training(self, trigger_type: str, actor_user_id: str | None) -> dict[str, Any]:
        with self._lock:
            active = self.storage.get_active_training_job()
            if active:
                return {
                    "enqueued": False,
                    "reason": "job_already_active",
                    "job": active,
                    "actor_user_id": actor_user_id,
                }

            sample_count = self._count_training_samples()
            if trigger_type == "scheduled" and sample_count < self.min_sample_threshold:
                return {
                    "enqueued": False,
                    "reason": "insufficient_samples",
                    "job": None,
                    "actor_user_id": actor_user_id,
                    "sample_count": sample_count,
                    "required_samples": self.min_sample_threshold,
                }

            if trigger_type == "scheduled":
                latest = self.storage.get_latest_training_job()
                if latest and self._is_cooldown_active(latest):
                    return {
                        "enqueued": False,
                        "reason": "cooldown_active",
                        "job": latest,
                        "actor_user_id": actor_user_id,
                        "cooldown_seconds": self.cooldown_seconds,
                    }

            job = self.storage.create_training_job(
                trigger_type=trigger_type,
                requested_by_user_id=actor_user_id,
            )

            thread = threading.Thread(
                target=self._run_job,
                args=(str(job["id"]),),
                name=f"training-job-{job['id']}",
                daemon=True,
            )
            thread.start()
            self.storage.create_training_model_action(
                action_type=trigger_type if trigger_type in {"force", "scheduled"} else "force",
                actor_user_id=actor_user_id,
                artifact_id=None,
                metadata={
                    "job_id": str(job["id"]),
                    "trigger_type": trigger_type,
                    "sample_count": sample_count,
                },
            )
            return {
                "enqueued": True,
                "reason": "queued",
                "job": job,
                "actor_user_id": actor_user_id,
            }

    def get_status(self) -> dict[str, Any]:
        active = self.storage.get_active_training_job()
        latest = self.storage.get_latest_training_job()
        latest_artifact = self.storage.get_latest_training_model_artifact()
        active_model = self.storage.get_active_training_model_artifact()
        candidate_model = self.storage.get_latest_candidate_training_model_artifact()
        state = "idle"
        if active:
            state = str(active.get("status") or "running")
        elif latest:
            state = str(latest.get("status") or "idle")
        return {
            "active_job": active,
            "latest_job": latest,
            "latest_artifact": latest_artifact,
            "active_model": active_model,
            "candidate_model": candidate_model,
            "promotion_thresholds": dict(self.promotion_thresholds),
            "state": state,
        }

    def list_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.storage.list_training_jobs(limit=max(1, limit))

    def list_actions(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.storage.list_training_model_actions(limit=max(1, limit))

    def promote_candidate(self, actor_user_id: str | None, artifact_id: str | None = None) -> dict[str, Any]:
        if artifact_id:
            candidate = self.storage.get_training_model_artifact(artifact_id)
            if candidate and candidate.get("model_status") != "candidate":
                candidate = None
        else:
            candidate = self.storage.get_latest_candidate_training_model_artifact()
        if not candidate:
            return {
                "promoted": False,
                "reason": "candidate_not_found",
                "candidate": None,
                "active_model": self.storage.get_active_training_model_artifact(),
                "gates": {
                    "passed": False,
                    "thresholds": dict(self.promotion_thresholds),
                    "checks": {},
                },
                "actor_user_id": actor_user_id,
            }

        metrics = candidate.get("metrics") or {}
        gates = self._evaluate_promotion_gates(metrics)
        if not gates["passed"]:
            return {
                "promoted": False,
                "reason": "gates_failed",
                "candidate": candidate,
                "active_model": self.storage.get_active_training_model_artifact(),
                "gates": gates,
                "actor_user_id": actor_user_id,
            }

        promoted = self.storage.promote_training_model_artifact(
            artifact_id=str(candidate["id"]),
            actor_user_id=actor_user_id,
            gate_results=gates,
        )
        self.storage.create_training_model_action(
            action_type="promote",
            actor_user_id=actor_user_id,
            artifact_id=str(promoted["id"]),
            metadata={"gates": gates},
        )
        self._log_event(
            "training_model_promoted",
            {"artifact_id": str(promoted["id"]), "actor_user_id": actor_user_id, "gates": gates},
        )
        return {
            "promoted": True,
            "reason": "promoted",
            "candidate": candidate,
            "active_model": promoted,
            "gates": gates,
            "actor_user_id": actor_user_id,
        }

    def rollback_active_model(self, actor_user_id: str | None) -> dict[str, Any]:
        try:
            restored = self.storage.rollback_training_model(actor_user_id=actor_user_id)
        except ValueError as exc:
            return {
                "rolled_back": False,
                "reason": str(exc),
                "active_model": self.storage.get_active_training_model_artifact(),
                "actor_user_id": actor_user_id,
            }

        self.storage.create_training_model_action(
            action_type="rollback",
            actor_user_id=actor_user_id,
            artifact_id=str(restored["id"]),
            metadata={"reason": "manual_rollback"},
        )
        self._log_event(
            "training_model_rollback",
            {"artifact_id": str(restored["id"]), "actor_user_id": actor_user_id},
        )
        return {
            "rolled_back": True,
            "reason": "rolled_back",
            "active_model": restored,
            "actor_user_id": actor_user_id,
        }

    def _run_job(self, job_id: str) -> None:
        self.storage.mark_training_job_running(job_id)
        try:
            dataset = self._build_dataset()
            if not dataset:
                self.storage.mark_training_job_failed(
                    job_id,
                    failure_reason="insufficient_samples",
                    trace_ref=None,
                    metadata={"dataset_size": 0},
                )
                return

            split = self._split_dataset(dataset)
            model_payload = self._train_model(split["train"])
            validation_metrics = self._compute_validation_metrics(
                rules=model_payload.get("rules") or {},
                validation_samples=split["validation"],
            )

            artifact_path = self.models_path / f"correction_model_v1_{job_id}.json"
            artifact_path.write_text(json.dumps(model_payload, ensure_ascii=True, indent=2), encoding="utf-8")

            dataset_hash = hashlib.sha256(
                json.dumps(dataset, sort_keys=True, ensure_ascii=True).encode("utf-8")
            ).hexdigest()

            artifact = self.storage.create_training_model_artifact(
                job_id=job_id,
                artifact_version="correction_model_v1",
                artifact_path=str(artifact_path),
                dataset_hash=dataset_hash,
                train_size=len(split["train"]),
                validation_size=len(split["validation"]),
                metrics={
                    "rules_count": model_payload.get("rules_count", 0),
                    "fields_covered": model_payload.get("fields_covered", 0),
                    "name_match_precision": validation_metrics["name_match_precision"],
                    "amount_parse_accuracy": validation_metrics["amount_parse_accuracy"],
                    "fallback_reduction": validation_metrics["fallback_reduction"],
                    "validation_samples": validation_metrics["validation_samples"],
                },
            )

            summary = {
                "dataset_size": len(dataset),
                "train_size": len(split["train"]),
                "validation_size": len(split["validation"]),
                "artifact_id": str(artifact.get("id")),
                "artifact_path": str(artifact.get("artifact_path")),
            }
            self.storage.mark_training_job_succeeded(job_id, summary)
            self._log_event("training_job_succeeded", {"job_id": job_id, **summary})
        except Exception as exc:
            trace_ref = str(uuid4())
            self._log_event(
                "training_job_failed",
                {
                    "job_id": job_id,
                    "trace_ref": trace_ref,
                    "error": str(exc),
                    "traceback": traceback.format_exc(),
                },
            )
            self.storage.mark_training_job_failed(
                job_id,
                failure_reason=str(exc),
                trace_ref=trace_ref,
                metadata={"failed_at": datetime.utcnow().isoformat()},
            )

    def _build_dataset(self) -> list[dict[str, Any]]:
        samples: list[dict[str, Any]] = []
        for sample_file in self.training_path.rglob("*.json"):
            if sample_file.is_file() and sample_file.parent != self.models_path:
                payload = self._read_json_with_retries(sample_file)
                if payload:
                    samples.append(payload)
        return sorted(samples, key=lambda item: str(item.get("created_at") or ""))

    def _count_training_samples(self) -> int:
        count = 0
        for sample_file in self.training_path.rglob("*.json"):
            if sample_file.is_file() and sample_file.parent != self.models_path:
                count += 1
        return count

    def _read_json_with_retries(self, sample_file: Path, retries: int = 2) -> dict[str, Any] | None:
        last_error = ""
        for attempt in range(retries + 1):
            try:
                return json.loads(sample_file.read_text(encoding="utf-8"))
            except Exception as exc:
                last_error = str(exc)
                self._log_event(
                    "training_dataset_read_retry",
                    {
                        "file": str(sample_file),
                        "attempt": attempt + 1,
                        "max_attempts": retries + 1,
                        "error": str(exc),
                    },
                )
        raise RuntimeError(f"dataset_read_failed:{sample_file}:{last_error}")

    @staticmethod
    def _split_dataset(dataset: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        train: list[dict[str, Any]] = []
        validation: list[dict[str, Any]] = []
        for sample in dataset:
            dedupe_key = str(sample.get("dedupe_key") or "")
            marker = int(hashlib.sha256(dedupe_key.encode("utf-8")).hexdigest(), 16) % 5
            if marker == 0:
                validation.append(sample)
            else:
                train.append(sample)

        if not train and validation:
            train.append(validation.pop())
        return {"train": train, "validation": validation}

    @staticmethod
    def _train_model(train_samples: list[dict[str, Any]]) -> dict[str, Any]:
        field_rules: dict[str, dict[str, str]] = {}
        vote_counter: dict[str, dict[str, dict[str, int]]] = {}

        for sample in train_samples:
            field = str(sample.get("field") or "").strip()
            raw = str(sample.get("ocr_read") or "").strip()
            corrected = str(sample.get("corrected") or "").strip()
            if not field or not raw or not corrected:
                continue
            vote_counter.setdefault(field, {}).setdefault(raw, {})
            vote_counter[field][raw][corrected] = vote_counter[field][raw].get(corrected, 0) + 1

        for field, raw_votes in vote_counter.items():
            field_rules[field] = {}
            for raw, corrected_votes in raw_votes.items():
                winner = sorted(corrected_votes.items(), key=lambda item: item[1], reverse=True)[0][0]
                field_rules[field][raw] = winner

        rules_count = sum(len(values) for values in field_rules.values())
        return {
            "model_version": "correction_model_v1",
            "trained_at": datetime.utcnow().isoformat(),
            "fields_covered": len(field_rules),
            "rules_count": rules_count,
            "rules": field_rules,
        }

    def _evaluate_promotion_gates(self, metrics: dict[str, Any]) -> dict[str, Any]:
        checks: dict[str, dict[str, Any]] = {}
        passed = True
        for key, threshold in self.promotion_thresholds.items():
            actual = float(metrics.get(key) or 0.0)
            check_passed = actual >= threshold
            checks[key] = {
                "actual": round(actual, 4),
                "threshold": round(float(threshold), 4),
                "passed": check_passed,
            }
            if not check_passed:
                passed = False
        return {
            "passed": passed,
            "thresholds": dict(self.promotion_thresholds),
            "checks": checks,
        }

    def _is_cooldown_active(self, latest_job: dict[str, Any]) -> bool:
        if self.cooldown_seconds <= 0:
            return False
        status = str(latest_job.get("status") or "").strip().lower()
        if status not in {"succeeded", "failed", "canceled"}:
            return False
        raw_finished = latest_job.get("finished_at") or latest_job.get("created_at")
        finished_at = self._coerce_datetime(raw_finished)
        if not finished_at:
            return False
        now_utc = datetime.now(timezone.utc)
        elapsed = (now_utc - finished_at).total_seconds()
        return elapsed < self.cooldown_seconds

    @staticmethod
    def _coerce_datetime(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value
        if not value:
            return None
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        if not normalized:
            return None
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    @staticmethod
    def _compute_validation_metrics(
        rules: dict[str, dict[str, str]],
        validation_samples: list[dict[str, Any]],
    ) -> dict[str, Any]:
        amount_fields = {
            "diezmo",
            "ofrenda",
            "primicias",
            "pro_templo",
            "ofrenda_misionera",
            "ofrenda_pastoral",
        }
        validation_total = len(validation_samples)
        fallback_hits = 0
        name_total = 0
        name_hits = 0
        amount_total = 0
        amount_hits = 0

        for sample in validation_samples:
            field = str(sample.get("field") or "").strip()
            raw = str(sample.get("ocr_read") or "").strip()
            corrected = str(sample.get("corrected") or "").strip()
            predicted = (rules.get(field) or {}).get(raw)
            if predicted:
                fallback_hits += 1
            if field == "member_name":
                name_total += 1
                if predicted and predicted == corrected:
                    name_hits += 1
            if field in amount_fields:
                amount_total += 1
                if predicted and TrainingJobService._same_numeric_value(predicted, corrected):
                    amount_hits += 1

        name_match_precision = (name_hits / name_total) if name_total > 0 else 1.0
        amount_parse_accuracy = (amount_hits / amount_total) if amount_total > 0 else 1.0
        fallback_reduction = (fallback_hits / validation_total) if validation_total > 0 else 0.0
        return {
            "name_match_precision": round(name_match_precision, 4),
            "amount_parse_accuracy": round(amount_parse_accuracy, 4),
            "fallback_reduction": round(fallback_reduction, 4),
            "validation_samples": validation_total,
        }

    @staticmethod
    def _same_numeric_value(left: str, right: str) -> bool:
        left_norm = str(left).replace(",", "").strip()
        right_norm = str(right).replace(",", "").strip()
        try:
            return float(left_norm) == float(right_norm)
        except ValueError:
            return False

    def _log_event(self, event: str, payload: dict[str, Any]) -> None:
        if not self.app_logger:
            return
        try:
            self.app_logger.info(json.dumps({"event": event, **payload}, ensure_ascii=True))
        except Exception:
            pass
