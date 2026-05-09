from typing import Any

from offering_app.repositories.postgresql_repo import PostgreSQLRepo


class CashWindowService:
    def __init__(self, storage: PostgreSQLRepo) -> None:
        self.storage = storage

    def open_session(self, service_date: str, actor_user_id: str | None, notes: str | None) -> dict[str, Any]:
        return self.storage.open_cash_session(service_date, actor_user_id, notes)

    def get_session(self, service_date: str) -> dict[str, Any] | None:
        return self.storage.get_cash_session(service_date)
