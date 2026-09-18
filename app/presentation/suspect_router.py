from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.presentation.security import CurrentUser, get_current_user
from app.services import suspect_service

router = APIRouter(prefix="/suspects", tags=["suspects"])


class SuspectOut(BaseModel):
    id: UUID
    full_name: str
    nationality: str


class SuspectCreate(BaseModel):
    full_name: str
    nationality: str


@router.get("", response_model=list[SuspectOut])
async def list_suspects(current_user: CurrentUser = Depends(get_current_user)):
    return await suspect_service.list_all_suspects()


@router.post("", response_model=SuspectOut)
async def create_suspect(payload: SuspectCreate, current_user: CurrentUser = Depends(get_current_user)):
    return await suspect_service.create_suspect(payload.full_name, payload.nationality)


@router.get("/{suspect_id}", response_model=SuspectOut)
async def get_suspect(suspect_id: UUID, current_user: CurrentUser = Depends(get_current_user)):
    suspect = await suspect_service.get_suspect(str(suspect_id))
    if suspect is None:
        raise HTTPException(status_code=404, detail="Suspect not found")
    return suspect
