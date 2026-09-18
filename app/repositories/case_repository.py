from app.db.connection import get_pool

CASE_COLUMNS = "id, case_type, status, requesting_agency, created_at"


async def list_cases() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(f"SELECT {CASE_COLUMNS} FROM case_record ORDER BY created_at DESC")
    return [dict(row) for row in rows]


async def get_case_by_id(case_id: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(f"SELECT {CASE_COLUMNS} FROM case_record WHERE id = $1", case_id)
    return dict(row) if row else None


async def create_case(case_type: str, requesting_agency: str) -> dict:
    pool = get_pool()
    row = await pool.fetchrow(
        "INSERT INTO case_record (case_type, requesting_agency) "
        "VALUES ($1, $2) "
        f"RETURNING {CASE_COLUMNS}",
        case_type,
        requesting_agency,
    )
    return dict(row)


async def update_case_status(case_id: str, status: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        "UPDATE case_record SET status = $2 WHERE id = $1 "
        f"RETURNING {CASE_COLUMNS}",
        case_id,
        status,
    )
    return dict(row) if row else None


async def delete_case(case_id: str) -> bool:
    pool = get_pool()
    result = await pool.execute("DELETE FROM case_record WHERE id = $1", case_id)
    return result == "DELETE 1"
