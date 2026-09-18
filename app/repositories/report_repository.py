from app.db.connection import get_pool

REPORT_COLUMNS = (
    "id, month, year, total_seizures, potential_loss_usd, potential_loss_sgd, "
    "most_affected_species, top_trafficker_nationality, status, "
    "approved_by_user_id, approved_at, created_at"
)


async def list_evidence_for_month(year: int, month: int) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT ei.case_id, ei.quantity, sp.common_name, sp.reference_value_usd "
        "FROM evidence_item ei "
        "JOIN species sp ON sp.id = ei.species_id "
        "WHERE EXTRACT(YEAR FROM ei.collection_date) = $1 "
        "AND EXTRACT(MONTH FROM ei.collection_date) = $2",
        year,
        month,
    )
    return [dict(row) for row in rows]


async def list_suspect_nationalities_for_month(year: int, month: int) -> list[str]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT s.nationality "
        "FROM case_suspect cs "
        "JOIN suspect s ON s.id = cs.suspect_id "
        "WHERE cs.case_id IN ("
        "  SELECT DISTINCT ei.case_id FROM evidence_item ei "
        "  WHERE EXTRACT(YEAR FROM ei.collection_date) = $1 "
        "  AND EXTRACT(MONTH FROM ei.collection_date) = $2"
        ")",
        year,
        month,
    )
    return [row["nationality"] for row in rows]


async def get_report_by_month(year: int, month: int) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        f"SELECT {REPORT_COLUMNS} FROM monthly_report WHERE year = $1 AND month = $2",
        year,
        month,
    )
    return dict(row) if row else None


async def get_report_by_id(report_id: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        f"SELECT {REPORT_COLUMNS} FROM monthly_report WHERE id = $1", report_id
    )
    return dict(row) if row else None


async def list_reports() -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(f"SELECT {REPORT_COLUMNS} FROM monthly_report ORDER BY year DESC, month DESC")
    return [dict(row) for row in rows]


async def create_report(
    month: int,
    year: int,
    total_seizures: int,
    potential_loss_usd,
    potential_loss_sgd,
    most_affected_species: str | None,
    top_trafficker_nationality: str | None,
) -> dict:
    pool = get_pool()
    row = await pool.fetchrow(
        "INSERT INTO monthly_report "
        "(month, year, total_seizures, potential_loss_usd, potential_loss_sgd, "
        "most_affected_species, top_trafficker_nationality) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7) "
        f"RETURNING {REPORT_COLUMNS}",
        month,
        year,
        total_seizures,
        potential_loss_usd,
        potential_loss_sgd,
        most_affected_species,
        top_trafficker_nationality,
    )
    return dict(row)


async def approve_report(report_id: str, approved_by_user_id: str) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        "UPDATE monthly_report "
        "SET status = 'approved', approved_by_user_id = $2, approved_at = now() "
        "WHERE id = $1 AND status = 'draft' "
        f"RETURNING {REPORT_COLUMNS}",
        report_id,
        approved_by_user_id,
    )
    return dict(row) if row else None


async def add_translation(report_id: str, language: str, narrative_text: str, pdf_key: str) -> dict:
    pool = get_pool()
    row = await pool.fetchrow(
        "INSERT INTO monthly_report_translation (report_id, language, narrative_text, pdf_key) "
        "VALUES ($1, $2, $3, $4) "
        "RETURNING id, report_id, language, narrative_text, pdf_key",
        report_id,
        language,
        narrative_text,
        pdf_key,
    )
    return dict(row)


async def list_translations(report_id: str) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT id, report_id, language, narrative_text, pdf_key "
        "FROM monthly_report_translation "
        "WHERE report_id = $1 "
        "ORDER BY language",
        report_id,
    )
    return [dict(row) for row in rows]
