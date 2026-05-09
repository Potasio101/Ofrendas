from datetime import date
from typing import Any

import psycopg
from psycopg.rows import dict_row

from offering_app.interfaces.i_storage_repo import IStorageRepo
from offering_app.models.offering import Offering


class PostgreSQLRepo(IStorageRepo):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def save(self, offering: Offering) -> str:
        offering.compute_total()
        service_date = offering.service_date or date.today()
        service_day = service_date.strftime("%A").lower()
        allowed_days = {"tuesday", "thursday", "sunday"}
        if service_day not in allowed_days:
            service_day = "sunday"
        query = """
            INSERT INTO offerings (
                service_date,
                service_day,
                member_name,
                payment_method,
                diezmo,
                ofrenda,
                primicias,
                pro_templo,
                ofrenda_misionera,
                ofrenda_pastoral,
                total,
                image_path,
                ocr_confidence,
                status,
                source_channel,
                captured_by_user_id,
                confirmed_by_user_id
            )
            VALUES (
                %(service_date)s,
                %(service_day)s,
                %(member_name)s,
                %(payment_method)s,
                %(diezmo)s,
                %(ofrenda)s,
                %(primicias)s,
                %(pro_templo)s,
                %(ofrenda_misionera)s,
                %(ofrenda_pastoral)s,
                %(total)s,
                %(image_path)s,
                %(ocr_confidence)s,
                'confirmed',
                'mobile',
                %(captured_by_user_id)s,
                %(confirmed_by_user_id)s
            )
            RETURNING id;
        """
        payload = {
            "service_date": service_date,
            "service_day": service_day,
            "member_name": offering.member_name,
            "payment_method": offering.payment_method,
            "diezmo": offering.diezmo,
            "ofrenda": offering.ofrenda,
            "primicias": offering.primicias,
            "pro_templo": offering.pro_templo,
            "ofrenda_misionera": offering.ofrenda_misionera,
            "ofrenda_pastoral": offering.ofrenda_pastoral,
            "total": offering.total,
            "image_path": offering.image_path,
            "ocr_confidence": offering.ocr_confidence,
            "captured_by_user_id": offering.captured_by_user_id,
            "confirmed_by_user_id": offering.confirmed_by_user_id,
        }
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, payload)
                row = cur.fetchone()
                return str(row["id"])

    def get_by_date(self, service_date: str) -> list[dict[str, Any]]:
        query = """
            SELECT id, service_date, member_name, total, review_status, created_at
            FROM offerings
            WHERE service_date = %(service_date)s
            ORDER BY created_at DESC;
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, {"service_date": service_date})
                return [dict(row) for row in cur.fetchall()]

    def get_daily_totals(self, service_date: str) -> dict[str, Any]:
        query = """
            SELECT
                COUNT(*) AS envelopes,
                COALESCE(SUM(total), 0) AS total,
                COALESCE(SUM(diezmo), 0) AS diezmo,
                COALESCE(SUM(ofrenda), 0) AS ofrenda
            FROM offerings
            WHERE service_date = %(service_date)s;
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, {"service_date": service_date})
                row = cur.fetchone()
                return dict(row) if row else {"envelopes": 0, "total": 0}

    def get_offering(self, offering_id: str) -> dict[str, Any] | None:
        query = "SELECT * FROM offerings WHERE id = %(offering_id)s"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, {"offering_id": offering_id})
                row = cur.fetchone()
                return dict(row) if row else None

    def update_offering_fields(
        self,
        offering_id: str,
        updates: dict[str, str],
        changed_by_user_id: str | None,
        reason: str | None,
    ) -> bool:
        if not updates:
            return True

        with self._connect() as conn:
            with conn.cursor() as cur:
                current = self.get_offering(offering_id)
                if not current:
                    return False

                for field_name, new_value in updates.items():
                    old_value = current.get(field_name)
                    self._insert_field_history(
                        cur,
                        offering_id=offering_id,
                        field_name=field_name,
                        old_value=str(old_value) if old_value is not None else None,
                        new_value=str(new_value),
                        changed_by_user_id=changed_by_user_id,
                        reason=reason,
                    )

                assignments = ", ".join(f"{field} = %({field})s" for field in updates)
                sql = f"UPDATE offerings SET {assignments}, updated_at = NOW() WHERE id = %(offering_id)s"
                payload = {**updates, "offering_id": offering_id}
                cur.execute(sql, payload)
            conn.commit()
        return True

    def _insert_field_history(
        self,
        cur,
        offering_id: str,
        field_name: str,
        old_value: str | None,
        new_value: str,
        changed_by_user_id: str | None,
        reason: str | None,
    ) -> None:
        query = """
            INSERT INTO offering_field_history (
                offering_id,
                field_name,
                old_value,
                new_value,
                change_type,
                changed_by_user_id,
                reason
            )
            VALUES (
                %(offering_id)s,
                %(field_name)s,
                %(old_value)s,
                %(new_value)s,
                'deferred_correction',
                %(changed_by_user_id)s,
                %(reason)s
            )
        """
        cur.execute(
            query,
            {
                "offering_id": offering_id,
                "field_name": field_name,
                "old_value": old_value,
                "new_value": new_value,
                "changed_by_user_id": changed_by_user_id,
                "reason": reason,
            },
        )
