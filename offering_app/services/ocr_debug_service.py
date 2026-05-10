import json
import logging
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np


class OcrDebugService:
    def __init__(
        self,
        base_path: str,
        enabled: bool,
        retention_days: int,
        max_sessions: int,
        logger: logging.Logger | None = None,
    ) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._enabled = bool(enabled)
        self.retention_days = max(1, int(retention_days))
        self.max_sessions = max(1, int(max_sessions))
        self._logger = logger or logging.getLogger(__name__)
        self._last_retention_run = 0.0

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> dict[str, Any]:
        self._enabled = bool(enabled)
        return self.get_status()

    def get_status(self) -> dict[str, Any]:
        return {
            "enabled": self._enabled,
            "retention_days": self.retention_days,
            "max_sessions": self.max_sessions,
            "base_path": str(self.base_path),
        }

    def write_session(
        self,
        request_id: str,
        input_image_path: str,
        preprocessed_image: np.ndarray,
        field_images: dict[str, np.ndarray],
        ocr_raw: dict[str, tuple[str, float]],
        parsed_fields: dict[str, Any],
        timings: dict[str, float],
        meta: dict[str, Any],
    ) -> bool:
        if not self._enabled:
            return False

        session_dir = self.base_path / request_id
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_image_path, session_dir / "input.jpg")
            cv2.imwrite(str(session_dir / "preprocessed.jpg"), preprocessed_image)
            self._write_roi_files(session_dir, field_images)
            self._write_json(
                session_dir / "ocr_raw.json",
                {
                    field: {"text": text, "confidence": confidence}
                    for field, (text, confidence) in ocr_raw.items()
                },
            )
            self._write_json(session_dir / "parsed_fields.json", parsed_fields)
            self._write_json(session_dir / "timings.json", timings)
            self._write_json(session_dir / "meta.json", meta)
            self.run_retention_job()
            return True
        except (OSError, ValueError, TypeError) as exc:
            self._logger.error(
                json.dumps(
                    {
                        "event": "ocr_debug_write_failed",
                        "request_id": request_id,
                        "error": str(exc),
                    },
                    ensure_ascii=True,
                )
            )
            return False

    def list_sessions(self, limit: int = 20) -> list[dict[str, Any]]:
        self.run_retention_job()
        safe_limit = max(1, min(int(limit), 100))
        session_dirs = sorted(
            [path for path in self.base_path.iterdir() if path.is_dir()],
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        sessions: list[dict[str, Any]] = []
        for session_dir in session_dirs[:safe_limit]:
            meta = self._read_json(session_dir / "meta.json")
            sessions.append(
                {
                    "request_id": session_dir.name,
                    "created_at": meta.get("created_at"),
                    "files": sorted(path.name for path in session_dir.iterdir() if path.is_file()),
                }
            )
        return sessions

    def get_session(self, request_id: str) -> dict[str, Any] | None:
        session_dir = self.base_path / request_id
        if not session_dir.exists() or not session_dir.is_dir():
            return None
        return {
            "request_id": request_id,
            "files": sorted(path.name for path in session_dir.iterdir() if path.is_file()),
            "meta": self._read_json(session_dir / "meta.json"),
            "timings": self._read_json(session_dir / "timings.json"),
            "ocr_raw": self._read_json(session_dir / "ocr_raw.json"),
            "parsed_fields": self._read_json(session_dir / "parsed_fields.json"),
        }

    def run_retention_job(self) -> None:
        now = time.time()
        if (now - self._last_retention_run) < 30:
            return
        self._last_retention_run = now

        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        sessions = sorted(
            [path for path in self.base_path.iterdir() if path.is_dir()],
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        for session_dir in sessions:
            modified_at = datetime.fromtimestamp(session_dir.stat().st_mtime, tz=timezone.utc)
            if modified_at < cutoff:
                shutil.rmtree(session_dir, ignore_errors=True)

        sessions = sorted(
            [path for path in self.base_path.iterdir() if path.is_dir()],
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        for extra in sessions[self.max_sessions :]:
            shutil.rmtree(extra, ignore_errors=True)

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        content = path.read_text(encoding="utf-8")
        return json.loads(content) if content.strip() else {}

    @staticmethod
    def _write_roi_files(session_dir: Path, field_images: dict[str, np.ndarray]) -> None:
        roi_map = {
            "member_name": "name_roi.jpg",
            "diezmo": "diezmo_roi.jpg",
            "ofrenda": "ofrenda_roi.jpg",
        }
        for field_name, filename in roi_map.items():
            roi = field_images.get(field_name)
            if roi is not None:
                cv2.imwrite(str(session_dir / filename), roi)
