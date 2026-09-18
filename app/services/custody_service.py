from app.repositories import custody_event_repository, evidence_item_repository


async def get_custody_history(evidence_item_id: str) -> list[dict]:
    return await custody_event_repository.list_by_evidence_item(evidence_item_id)


async def record_transfer(
    evidence_item_id: str,
    recorded_by_user_id: str,
    handed_from: str,
    handed_to: str,
) -> dict | None:
    evidence_item = await evidence_item_repository.get_by_id(evidence_item_id)
    if evidence_item is None:
        return None
    return await custody_event_repository.create_custody_event(
        evidence_item_id, recorded_by_user_id, handed_from, handed_to
    )
