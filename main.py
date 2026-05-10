import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from offering_app.config import AppConfig, ensure_data_dirs
from offering_app.repositories.postgresql_repo import PostgreSQLRepo
from offering_app.repositories.training_repo import TrainingRepo
from offering_app.services.image_processor import ImageProcessor
from offering_app.services.offering_service import OfferingService
from offering_app.services.training_job_service import TrainingJobService
from offering_app.strategies.easyocr_strategy import EasyOCRStrategy
from offering_app.strategies.fuzzy_correction import FuzzyCorrection
from offering_app.ui.app import create_app


logger = logging.getLogger(__name__)


def load_members(repo: PostgreSQLRepo) -> list[str]:
    try:
        names = repo.list_active_member_names()
        if names:
            return names
    except Exception as exc:
        logger.warning("Could not load active members from repository; using fallback list", exc_info=exc)
    return ["Miembro Desconocido"]


def _build_training_scheduler(training_job_service: TrainingJobService) -> BackgroundScheduler | None:
    enabled = str(os.getenv("TRAINING_SCHEDULER_ENABLED", "true")).strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return None
    hour = max(0, min(23, int(os.getenv("TRAINING_SCHEDULE_HOUR", "2"))))
    minute = max(0, min(59, int(os.getenv("TRAINING_SCHEDULE_MINUTE", "0"))))
    timezone_name = str(os.getenv("APP_TIMEZONE", "UTC")).strip() or "UTC"
    scheduler = BackgroundScheduler(timezone=timezone_name)
    scheduler.add_job(
        training_job_service.trigger_scheduled_training,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone_name),
        id="nightly-training-job",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info("Training scheduler enabled at %02d:%02d (%s)", hour, minute, timezone_name)
    return scheduler


def build_app():
    load_dotenv()
    config = AppConfig()
    ensure_data_dirs(config)

    ocr = EasyOCRStrategy()
    corrector = FuzzyCorrection()
    storage = PostgreSQLRepo(config.database_url)
    training = TrainingRepo(config.training_path)
    processor = ImageProcessor()
    members = load_members(storage)

    service = OfferingService(
        ocr=ocr,
        corrector=corrector,
        storage=storage,
        training=training,
        processor=processor,
        members=members,
    )
    training_job_service = TrainingJobService(
        storage=storage,
        training_path=config.training_path,
        app_logger=logger,
        min_sample_threshold=int(os.getenv("TRAINING_MIN_SAMPLE_THRESHOLD", "10")),
        cooldown_seconds=int(os.getenv("TRAINING_COOLDOWN_SECONDS", "3600")),
        promotion_thresholds={
            "name_match_precision": float(os.getenv("TRAINING_PROMOTION_MIN_NAME_PRECISION", "0.85")),
            "amount_parse_accuracy": float(os.getenv("TRAINING_PROMOTION_MIN_AMOUNT_ACCURACY", "0.9")),
            "fallback_reduction": float(os.getenv("TRAINING_PROMOTION_MIN_FALLBACK_REDUCTION", "0.2")),
        },
    )
    app = create_app(
        service=service,
        storage=storage,
        upload_path=config.upload_path,
        training_job_service=training_job_service,
    )
    scheduler = _build_training_scheduler(training_job_service)
    if scheduler:
        app.extensions["training_scheduler"] = scheduler
    return (app, config)


if __name__ == "__main__":
    app, cfg = build_app()
    app.run(host=cfg.host, port=cfg.port, debug=cfg.flask_debug)
