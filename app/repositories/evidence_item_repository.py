from datetime import date

from app.db.connection import get_pool

EVIDENCE_ITEM_COLUMNS = (
    "id, case_id, species_id, description, quantity, unit, collection_date, photo_key, created_at"
)


async def list_by_case(case_id: str) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        f"SELECT {EVIDENCE_ITEM_COLUMNS} FROM evidence_item WHERE case_id = $1 ORDER BY collection_date",
        case_id,
    )
    return [dict(row) for row in rows]


async def get_by_id(evidence_item_id: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        f"SELECT {EVIDENCE_ITEM_COLUMNS} FROM evidence_item WHERE id = $1",
        evidence_item_id,
    )
    return dict(row) if row else None


async def create(
    case_id: str,
    species_id: str,
    description: str,
    quantity: float,
    unit: str,
    collection_date: date,
    connection=None,
) -> dict:
    executor = connection if connection is not None else get_pool()
    row = await executor.fetchrow(
        "INSERT INTO evidence_item (case_id, species_id, description, quantity, unit, collection_date) "
        "VALUES ($1, $2, $3, $4, $5, $6) "
        f"RETURNING {EVIDENCE_ITEM_COLUMNS}",
        case_id,
        species_id,
        description,
        quantity,
        unit,
        collection_date,
    )
    return dict(row)


async def list_by_case_with_species_value(case_id: str) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT ei.id, ei.quantity, sp.reference_value_usd "
        "FROM evidence_item ei "
        "JOIN species sp ON sp.id = ei.species_id "
        "WHERE ei.case_id = $1",
        case_id,
    )
    return [dict(row) for row in rows]


async def set_photo_key(evidence_item_id: str, photo_key: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        "UPDATE evidence_item SET photo_key = $2 WHERE id = $1 "
        f"RETURNING {EVIDENCE_ITEM_COLUMNS}",
        evidence_item_id,
        photo_key,
    )
    return dict(row) if row else None


async def delete(evidence_item_id: str) -> bool:
    pool = get_pool()
    result = await pool.execute("DELETE FROM evidence_item WHERE id = $1", evidence_item_id)
    return result == "DELETE 1"
