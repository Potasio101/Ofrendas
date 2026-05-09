from pathlib import Path


class LocalExportRepo:
    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def build_export_path(self, provider: str, period_key: str) -> Path:
        period_dir = self.base_path / provider / period_key
        period_dir.mkdir(parents=True, exist_ok=True)
        return period_dir
