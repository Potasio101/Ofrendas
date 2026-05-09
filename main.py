from dotenv import load_dotenv

from offering_app.config import AppConfig, ensure_data_dirs
from offering_app.repositories.postgresql_repo import PostgreSQLRepo
from offering_app.repositories.training_repo import TrainingRepo
from offering_app.services.image_processor import ImageProcessor
from offering_app.services.offering_service import OfferingService
from offering_app.strategies.easyocr_strategy import EasyOCRStrategy
from offering_app.strategies.fuzzy_correction import FuzzyCorrection
from offering_app.ui.app import create_app


def load_members(repo: PostgreSQLRepo) -> list[str]:
    query = "SELECT full_name FROM users WHERE is_active = TRUE ORDER BY full_name"
    try:
        with repo._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                names = [str(row["full_name"]) for row in rows]
                if names:
                    return names
    except Exception:
        pass
    return ["Miembro Desconocido"]


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
    return create_app(service=service, storage=storage, upload_path=config.upload_path), config


if __name__ == "__main__":
    app, cfg = build_app()
    app.run(host=cfg.host, port=cfg.port, debug=cfg.flask_debug)
