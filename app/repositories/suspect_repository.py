from app.db.connection import get_pool


async def list_suspects() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch("SELECT id, full_name, nationality FROM suspect ORDER BY full_name")
    return [dict(row) for row in rows]


async def get_by_id(suspect_id: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT id, full_name, nationality FROM suspect WHERE id = $1", suspect_id
    )
    return dict(row) if row else None


async def create(full_name: str, nationality: str) -> dict:
    pool = get_pool()
    row = await pool.fetchrow(
        "INSERT INTO suspect (full_name, nationality) VALUES ($1, $2) "
        "RETURNING id, full_name, nationality",
        full_name,
        nationality,
    )
    return dict(row)


async def link_to_case(case_id: str, suspect_id: str, role_in_case: str | None) -> dict:
    pool = get_pool()
    row = await pool.fetchrow(
        "INSERT INTO case_suspect (case_id, suspect_id, role_in_case) "
        "VALUES ($1, $2, $3) "
        "RETURNING case_id, suspect_id, role_in_case",
        case_id,
        suspect_id,
        role_in_case,
    )
    return dict(row)


async def list_by_case(case_id: str) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT s.id, s.full_name, s.nationality, cs.role_in_case "
        "FROM suspect s "
        "JOIN case_suspect cs ON cs.suspect_id = s.id "
        "WHERE cs.case_id = $1 "
        "ORDER BY s.full_name",
        case_id,
    )
    return [dict(row) for row in rows]
