from decimal import Decimal

import pytest

from app.db.connection import get_pool
from app.services import case_service

SEEDED_CASE_ID = "40000000-0000-0000-0000-000000000001"


async def _sum_with_raw_sql(case_id: str) -> Decimal:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT SUM(ei.quantity * sp.reference_value_usd) AS total "
        "FROM evidence_item ei "
        "JOIN species sp ON sp.id = ei.species_id "
        "WHERE ei.case_id = $1",
        case_id,
    )
    return row["total"]


@pytest.mark.asyncio
async def test_potential_loss_matches_independent_sql_calculation():
    production_result = await case_service.calculate_potential_loss_usd(SEEDED_CASE_ID)
    independent_result = await _sum_with_raw_sql(SEEDED_CASE_ID)

    assert production_result == independent_result


@pytest.mark.asyncio
async def test_potential_loss_matches_hand_calculated_value():
    # pangolin 12.5kg*250 + ivory 3.2kg*1500 + turtle 1.8kg*600 + gecko 20*50
    expected = Decimal("3125.00000") + Decimal("4800.00000") + Decimal("1080.00000") + Decimal("1000.00000")

    result = await case_service.calculate_potential_loss_usd(SEEDED_CASE_ID)

    assert result == expected
