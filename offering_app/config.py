import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    app_env: str = os.getenv("APP_ENV", "local")
    host: str = os.getenv("HOST", "127.0.0.1")
    port: int = int(os.getenv("PORT", "5000"))
    flask_debug: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    database_url: str = os.getenv("DATABASE_URL", "postgresql://ofrendas:ofrendas@localhost:5432/ofrendas")

    ocr_strategy: str = os.getenv("OCR_STRATEGY", "easyocr")
    correction_strategy: str = os.getenv("CORRECTION_STRATEGY", "fuzzy")
    storage_backend: str = os.getenv("STORAGE_BACKEND", "postgresql")

    training_path: str = os.getenv("TRAINING_PATH", "./data/training")
    local_export_path: str = os.getenv("LOCAL_EXPORT_PATH", "./data/exports")
    upload_path: str = os.getenv("UPLOAD_PATH", "./data/uploads")


FIELD_COORDS: dict[str, tuple[float, float, float, float]] = {
    "member_name": (0.08, 0.11, 0.84, 0.08),
    "diezmo": (0.08, 0.25, 0.25, 0.08),
    "ofrenda": (0.37, 0.25, 0.25, 0.08),
    "primicias": (0.66, 0.25, 0.25, 0.08),
    "pro_templo": (0.08, 0.36, 0.25, 0.08),
    "ofrenda_misionera": (0.37, 0.36, 0.25, 0.08),
    "ofrenda_pastoral": (0.66, 0.36, 0.25, 0.08),
    "service_date": (0.08, 0.47, 0.35, 0.08),
    "payment_method": (0.66, 0.47, 0.25, 0.08),
}


def ensure_data_dirs(config: AppConfig) -> None:
    Path(config.training_path).mkdir(parents=True, exist_ok=True)
    Path(config.local_export_path).mkdir(parents=True, exist_ok=True)
    Path(config.upload_path).mkdir(parents=True, exist_ok=True)
