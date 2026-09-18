from app.repositories import suspect_repository


async def list_all_suspects() -> list[dict]:
    return await suspect_repository.list_suspects()


async def get_suspect(suspect_id: str) -> dict | None:
    return await suspect_repository.get_by_id(suspect_id)


async def create_suspect(full_name: str, nationality: str) -> dict:
    return await suspect_repository.create(full_name, nationality)


async def link_suspect_to_case(case_id: str, suspect_id: str, role_in_case: str | None) -> dict:
    return await suspect_repository.link_to_case(case_id, suspect_id, role_in_case)


async def list_suspects_for_case(case_id: str) -> list[dict]:
    return await suspect_repository.list_by_case(case_id)
