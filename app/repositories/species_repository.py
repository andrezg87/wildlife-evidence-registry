from app.db.connection import get_pool


async def list_species() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT id, common_name, scientific_name, seized_part, unit, reference_value_usd "
        "FROM species "
        "ORDER BY common_name"
    )
    return [dict(row) for row in rows]


async def get_species_by_id(species_id: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT id, common_name, scientific_name, seized_part, unit, reference_value_usd "
        "FROM species "
        "WHERE id = $1",
        species_id,
    )
    return dict(row) if row else None
