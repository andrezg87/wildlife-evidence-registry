from app.db.connection import get_pool

CUSTODY_EVENT_COLUMNS = "id, evidence_item_id, recorded_by_user_id, handed_from, handed_to, occurred_at"


async def create_custody_event(
    evidence_item_id: str,
    recorded_by_user_id: str,
    handed_from: str,
    handed_to: str,
    connection=None,
) -> dict:
    executor = connection if connection is not None else get_pool()
    row = await executor.fetchrow(
        "INSERT INTO custody_event (evidence_item_id, recorded_by_user_id, handed_from, handed_to) "
        "VALUES ($1, $2, $3, $4) "
        f"RETURNING {CUSTODY_EVENT_COLUMNS}",
        evidence_item_id,
        recorded_by_user_id,
        handed_from,
        handed_to,
    )
    return dict(row)


async def list_by_evidence_item(evidence_item_id: str) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        f"SELECT {CUSTODY_EVENT_COLUMNS} FROM custody_event WHERE evidence_item_id = $1 ORDER BY occurred_at",
        evidence_item_id,
    )
    return [dict(row) for row in rows]
