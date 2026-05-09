from datetime import date
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from offering_app.interfaces.i_storage_repo import IStorageRepo
from offering_app.models.offering import Offering


class PostgreSQLRepo(IStorageRepo):
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, row_factory=dict_row)

    def get_current_service_date(self, timezone_name: str) -> str:
        query = "SELECT (NOW() AT TIME ZONE %(timezone)s)::date AS service_date"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, {"timezone": timezone_name})
                row = cur.fetchone()
                return row["service_date"].isoformat()

    @staticmethod
    def _normalize_uuid(value: str | None) -> str | None:
        if not value:
            return None
        candidate = str(value).strip()
        if not candidate:
            return None
        try:
            return str(UUID(candidate))
        except (ValueError, TypeError):
            return None

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

    def open_cash_session(
        self,
        service_date: str,
        opened_by_user_id: str | None,
        notes: str | None,
    ) -> dict[str, Any]:
        safe_user_id = self._normalize_uuid(opened_by_user_id)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cash_sessions (service_date, session_status, notes, opened_by_user_id)
                    VALUES (%(service_date)s, 'open', %(notes)s, %(opened_by_user_id)s)
                    ON CONFLICT (service_date) DO NOTHING
                    RETURNING id
                    """,
                    {
                        "service_date": service_date,
                        "notes": notes,
                        "opened_by_user_id": safe_user_id,
                    },
                )
                created_row = cur.fetchone()
                cur.execute(
                    """
                    SELECT id, service_date, session_status, expected_cash_total, counted_cash_total, variance_total, notes
                    FROM cash_sessions
                    WHERE service_date = %(service_date)s
                    LIMIT 1
                    """,
                    {"service_date": service_date},
                )
                session_row = cur.fetchone()
                session = dict(session_row) if session_row else None
                if not session:
                    raise RuntimeError("Failed to open or retrieve cash session")
                if created_row:
                    cur.execute(
                        """
                        INSERT INTO cash_session_events (cash_session_id, event_type, actor_user_id, metadata)
                        VALUES (%(cash_session_id)s, 'open', %(actor_user_id)s, '{}'::jsonb)
                        """,
                        {
                            "cash_session_id": session["id"],
                            "actor_user_id": safe_user_id,
                        },
                    )
                conn.commit()
                session["created"] = bool(created_row)
                return session

    def get_cash_session(self, service_date: str) -> dict[str, Any] | None:
        query = """
            SELECT id, service_date, session_status, expected_cash_total, counted_cash_total, variance_total, notes
            FROM cash_sessions
            WHERE service_date = %(service_date)s
            LIMIT 1
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, {"service_date": service_date})
                row = cur.fetchone()
                return dict(row) if row else None

    def create_disbursement_draft(self, payload: dict[str, Any], created_by_user_id: str | None) -> dict[str, Any]:
        safe_user_id = self._normalize_uuid(created_by_user_id)
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO disbursements (
                        output_date,
                        category,
                        description,
                        beneficiary_name,
                        amount,
                        fund_source_code,
                        status,
                        justification,
                        created_by_user_id
                    )
                    VALUES (
                        %(output_date)s,
                        %(category)s,
                        %(description)s,
                        %(beneficiary_name)s,
                        %(amount)s,
                        %(fund_source_code)s,
                        'draft',
                        %(justification)s,
                        %(created_by_user_id)s
                    )
                    RETURNING id, output_date, category, description, beneficiary_name, amount, fund_source_code, status
                    """,
                    {
                        "output_date": payload["output_date"],
                        "category": payload.get("category", "other"),
                        "description": payload["description"],
                        "beneficiary_name": payload.get("beneficiary_name"),
                        "amount": float(payload["amount"]),
                        "fund_source_code": payload.get("fund_source_code", "other"),
                        "justification": payload.get("justification"),
                        "created_by_user_id": safe_user_id,
                    },
                )
                row = cur.fetchone()
                if not row:
                    raise RuntimeError("Failed to create disbursement draft")
                cur.execute(
                    """
                    INSERT INTO disbursement_events (disbursement_id, event_type, actor_user_id, metadata)
                    VALUES (%(disbursement_id)s, 'created', %(actor_user_id)s, '{}'::jsonb)
                    """,
                    {
                        "disbursement_id": row["id"],
                        "actor_user_id": safe_user_id,
                    },
                )
                conn.commit()
                return dict(row)

    def list_disbursement_drafts(self, output_date: str | None) -> list[dict[str, Any]]:
        base_query = """
            SELECT id, output_date, category, description, beneficiary_name, amount, fund_source_code, status, created_at
            FROM disbursements
            WHERE status = 'draft'
        """
        params: dict[str, Any] = {}
        if output_date:
            base_query += " AND output_date = %(output_date)s"
            params["output_date"] = output_date
        base_query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(base_query, params)
                return [dict(row) for row in cur.fetchall()]
