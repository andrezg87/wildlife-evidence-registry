from decimal import Decimal

from app.repositories import case_repository, evidence_item_repository


async def list_all_cases() -> list[dict]:
    return await case_repository.list_cases()


async def get_case(case_id: str) -> dict | None:
    return await case_repository.get_case_by_id(case_id)


async def create_case(case_type: str, requesting_agency: str) -> dict:
    return await case_repository.create_case(case_type, requesting_agency)


async def update_case_status(case_id: str, status: str) -> dict | None:
    return await case_repository.update_case_status(case_id, status)


async def delete_case(case_id: str) -> bool:
    return await case_repository.delete_case(case_id)


async def calculate_potential_loss_usd(case_id: str) -> Decimal:
    items = await evidence_item_repository.list_by_case_with_species_value(case_id)
    return sum(
        (item["quantity"] * item["reference_value_usd"] for item in items),
        Decimal("0"),
    )
