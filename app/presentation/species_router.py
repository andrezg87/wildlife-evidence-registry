from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import species_service

router = APIRouter(prefix="/species", tags=["species"])


class SpeciesOut(BaseModel):
    id: UUID
    common_name: str
    scientific_name: str
    seized_part: str
    unit: str
    reference_value_usd: float


@router.get("", response_model=list[SpeciesOut])
async def list_species():
    return await species_service.list_all_species()


@router.get("/{species_id}", response_model=SpeciesOut)
async def get_species(species_id: str):
    species = await species_service.get_species(species_id)
    if species is None:
        raise HTTPException(status_code=404, detail="Species not found")
    return species
