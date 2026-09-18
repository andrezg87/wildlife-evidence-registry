from app.repositories import species_repository


async def list_all_species() -> list[dict]:
    return await species_repository.list_species()


async def get_species(species_id: str) -> dict | None:
    return await species_repository.get_species_by_id(species_id)
