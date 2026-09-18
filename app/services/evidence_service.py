from datetime import date

from app.db.connection import get_pool
from app.repositories import custody_event_repository, evidence_item_repository


async def list_evidence_for_case(case_id: str) -> list[dict]:
    return await evidence_item_repository.list_by_case(case_id)


async def get_evidence_item(evidence_item_id: str) -> dict | None:
    return await evidence_item_repository.get_by_id(evidence_item_id)


async def register_evidence_item(
    case_id: str,
    species_id: str,
    description: str,
    quantity: float,
    unit: str,
    collection_date: date,
    recorded_by_user_id: str,
    collected_by: str,
) -> dict:
    pool = get_pool()
    async with pool.acquire() as connection:
        async with connection.transaction():
            evidence_item = await evidence_item_repository.create(
                case_id,
                species_id,
                description,
                quantity,
                unit,
                collection_date,
                connection=connection,
            )
            await custody_event_repository.create_custody_event(
                evidence_item_id=str(evidence_item["id"]),
                recorded_by_user_id=recorded_by_user_id,
                handed_from=collected_by,
                handed_to="Straits Trace Labs evidence intake",
                connection=connection,
            )
    return evidence_item


async def set_evidence_photo(evidence_item_id: str, photo_url: str) -> dict | None:
    return await evidence_item_repository.set_photo_url(evidence_item_id, photo_url)


async def delete_evidence_item(evidence_item_id: str) -> bool:
    return await evidence_item_repository.delete(evidence_item_id)
