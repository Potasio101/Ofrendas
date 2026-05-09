from typing import Any

from offering_app.repositories.postgresql_repo import PostgreSQLRepo


class CashWindowService:
    def __init__(self, storage: PostgreSQLRepo) -> None:
        self.storage = storage

    def open_session(self, service_date: str, actor_user_id: str | None, notes: str | None) -> dict[str, Any]:
        return self.storage.open_cash_session(service_date, actor_user_id, notes)

    def get_session(self, service_date: str) -> dict[str, Any] | None:
        return self.storage.get_cash_session(service_date)

    def upsert_line(
        self,
        service_date: str,
        denomination_value: float,
        denomination_type: str,
        quantity: int,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        return self.storage.upsert_cash_count_line(
            service_date=service_date,
            denomination_value=denomination_value,
            denomination_type=denomination_type,
            quantity=quantity,
            actor_user_id=actor_user_id,
        )

    def close_session(self, service_date: str, actor_user_id: str | None, notes: str | None) -> dict[str, Any]:
        return self.storage.close_cash_session(service_date, actor_user_id, notes)

    def reopen_session(self, service_date: str, actor_user_id: str | None, reason: str | None) -> dict[str, Any]:
        return self.storage.reopen_cash_session(service_date, actor_user_id, reason)
