from datetime import date, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.presentation.security import CurrentUser, get_current_user, require_lab_director
from app.services import custody_service, evidence_service

router = APIRouter(prefix="/evidence", tags=["evidence"])


class EvidenceOut(BaseModel):
    id: UUID
    case_id: UUID
    species_id: UUID
    description: str
    quantity: float
    unit: Literal["kg", "unit"]
    collection_date: date
    photo_url: str | None
    created_at: datetime


class CustodyEventOut(BaseModel):
    id: UUID
    evidence_item_id: UUID
    recorded_by_user_id: UUID
    handed_from: str
    handed_to: str
    occurred_at: datetime


class CustodyTransferCreate(BaseModel):
    handed_from: str
    handed_to: str


@router.get("/{evidence_id}", response_model=EvidenceOut)
async def get_evidence_item(evidence_id: UUID, current_user: CurrentUser = Depends(get_current_user)):
    evidence = await evidence_service.get_evidence_item(str(evidence_id))
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence item not found")
    return evidence


@router.delete("/{evidence_id}", status_code=204)
async def delete_evidence_item(
    evidence_id: UUID, current_user: CurrentUser = Depends(require_lab_director)
):
    deleted = await evidence_service.delete_evidence_item(str(evidence_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Evidence item not found")


@router.post("/{evidence_id}/photo", response_model=EvidenceOut)
async def upload_evidence_photo(
    evidence_id: UUID,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
):
    evidence = await evidence_service.upload_evidence_photo(
        str(evidence_id), file.filename, file.file
    )
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence item not found")
    return evidence


@router.get("/{evidence_id}/custody-events", response_model=list[CustodyEventOut])
async def list_custody_events(
    evidence_id: UUID, current_user: CurrentUser = Depends(get_current_user)
):
    return await custody_service.get_custody_history(str(evidence_id))


@router.post("/{evidence_id}/custody-events", response_model=CustodyEventOut)
async def record_custody_event(
    evidence_id: UUID,
    payload: CustodyTransferCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    event = await custody_service.record_transfer(
        evidence_item_id=str(evidence_id),
        recorded_by_user_id=current_user.user_id,
        handed_from=payload.handed_from,
        handed_to=payload.handed_to,
    )
    if event is None:
        raise HTTPException(status_code=404, detail="Evidence item not found")
    return event
