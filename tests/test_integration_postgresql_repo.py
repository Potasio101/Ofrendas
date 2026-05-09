import os
import uuid
from datetime import date

import psycopg

from offering_app.models.offering import Offering
from offering_app.repositories.postgresql_repo import PostgreSQLRepo


def _database_url() -> str:
    return os.getenv("DATABASE_URL", "postgresql://ofrendas:ofrendas@localhost:5432/ofrendas")


def test_postgresql_repo_save_get_and_field_history_integration():
    repo = PostgreSQLRepo(_database_url())
    unique_name = f"Test Member {uuid.uuid4().hex[:8]}"

    offering = Offering(
        member_name=unique_name,
        diezmo=12.5,
        ofrenda=7.5,
        primicias=1.0,
        pro_templo=2.0,
        ofrenda_misionera=3.0,
        ofrenda_pastoral=4.0,
        service_date=date.today(),
        payment_method="cash",
        image_path="/tmp/test-envelope.jpg",
        ocr_confidence=0.88,
    )

    offering_id = repo.save(offering)
    assert offering_id

    rows = repo.get_by_date(date.today().isoformat())
    assert any(str(r["id"]) == offering_id for r in rows)

    ok = repo.update_offering_fields(
        offering_id=offering_id,
        updates={"member_name": f"{unique_name} Updated", "payment_method": "zelle"},
        changed_by_user_id=None,
        reason="integration test",
    )
    assert ok is True

    ok_amounts = repo.update_offering_fields(
        offering_id=offering_id,
        updates={"diezmo": "20.0", "ofrenda": "5.0"},
        changed_by_user_id=None,
        reason="integration total recalculation",
    )
    assert ok_amounts is True

    with psycopg.connect(_database_url()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT total FROM offerings WHERE id = %s", (offering_id,))
            total_value = float(cur.fetchone()[0])
            assert total_value == 35.0

            cur.execute(
                """
                SELECT count(*)
                FROM offering_field_history
                WHERE offering_id = %s
                """,
                (offering_id,),
            )
            history_count = cur.fetchone()[0]
            assert history_count >= 2

            cur.execute("DELETE FROM offering_field_history WHERE offering_id = %s", (offering_id,))
            cur.execute("DELETE FROM offerings WHERE id = %s", (offering_id,))
        conn.commit()
