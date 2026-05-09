from typing import Any

from offering_app.repositories.postgresql_repo import PostgreSQLRepo


class KioskPOSService:
    def __init__(self, storage: PostgreSQLRepo) -> None:
        self.storage = storage

    def get_or_create_open_order(self, service_date: str, actor_user_id: str | None, notes: str | None) -> dict[str, Any]:
        return self.storage.get_or_create_open_kiosk_order(service_date, actor_user_id, notes)

    def list_items(self, active_only: bool = True) -> list[dict[str, Any]]:
        return self.storage.list_kiosk_items(active_only=active_only)

    def add_catalog_line(
        self,
        kiosk_order_id: str,
        kiosk_item_id: str,
        quantity: int,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        return self.storage.add_kiosk_catalog_line(kiosk_order_id, kiosk_item_id, quantity, actor_user_id)

    def add_custom_line(
        self,
        kiosk_order_id: str,
        item_name: str,
        unit_price: float,
        quantity: int,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        return self.storage.add_kiosk_custom_line(
            kiosk_order_id=kiosk_order_id,
            item_name=item_name,
            unit_price=unit_price,
            quantity=quantity,
            actor_user_id=actor_user_id,
        )

    def pay_order(
        self,
        kiosk_order_id: str,
        payment_method: str,
        amount_paid: float,
        cash_received: float | None,
        zelle_customer_name: str | None,
        transaction_reference: str | None,
        actor_user_id: str | None,
    ) -> dict[str, Any]:
        return self.storage.pay_kiosk_order(
            kiosk_order_id=kiosk_order_id,
            payment_method=payment_method,
            amount_paid=amount_paid,
            cash_received=cash_received,
            zelle_customer_name=zelle_customer_name,
            transaction_reference=transaction_reference,
            actor_user_id=actor_user_id,
        )
