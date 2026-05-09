from typing import Any

from offering_app.repositories.postgresql_repo import PostgreSQLRepo


class OutputsService:
    def __init__(self, storage: PostgreSQLRepo) -> None:
        self.storage = storage

    def create_draft(self, payload: dict[str, Any], actor_user_id: str | None) -> dict[str, Any]:
        return self.storage.create_disbursement_draft(payload, actor_user_id)

    def list_drafts(self, output_date: str | None) -> list[dict[str, Any]]:
        return self.storage.list_disbursement_drafts(output_date)
