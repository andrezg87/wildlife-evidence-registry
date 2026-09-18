import asyncio
from datetime import date
from typing import BinaryIO
from uuid import uuid4

from app.db.connection import get_pool
from app.repositories import custody_event_repository, evidence_item_repository, storage_repository


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


async def upload_evidence_photo(
    evidence_item_id: str, filename: str, file_obj: BinaryIO
) -> dict | None:
    key = f"evidence/{evidence_item_id}/{uuid4()}_{filename}"
    photo_url = await asyncio.to_thread(storage_repository.upload_file, key, file_obj)
    return await evidence_item_repository.set_photo_url(evidence_item_id, photo_url)


async def delete_evidence_item(evidence_item_id: str) -> bool:
    return await evidence_item_repository.delete(evidence_item_id)
