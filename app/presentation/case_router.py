from datetime import date, datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.presentation.security import CurrentUser, get_current_user, require_lab_director
from app.services import case_service, evidence_service, suspect_service

router = APIRouter(prefix="/cases", tags=["cases"])

CaseType = Literal["airport_seizure", "port_seizure", "other_seizure"]
CaseStatus = Literal["open", "under_analysis", "closed"]


class CaseOut(BaseModel):
    id: UUID
    case_type: CaseType
    status: CaseStatus
    requesting_agency: str
    created_at: datetime


class CaseCreate(BaseModel):
    case_type: CaseType
    requesting_agency: str


class CaseStatusUpdate(BaseModel):
    status: CaseStatus


class PotentialLossOut(BaseModel):
    case_id: UUID
    potential_loss_usd: float
    potential_loss_sgd: float


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


class EvidenceCreate(BaseModel):
    species_id: UUID
    description: str
    quantity: float
    unit: Literal["kg", "unit"]
    collection_date: date
    collected_by: str


class SuspectOut(BaseModel):
    id: UUID
    full_name: str
    nationality: str
    role_in_case: str | None = None


class SuspectLinkCreate(BaseModel):
    suspect_id: UUID
    role_in_case: str | None = None


@router.get("", response_model=list[CaseOut])
async def list_cases(current_user: CurrentUser = Depends(get_current_user)):
    return await case_service.list_all_cases()


@router.post("", response_model=CaseOut)
async def create_case(payload: CaseCreate, current_user: CurrentUser = Depends(get_current_user)):
    return await case_service.create_case(payload.case_type, payload.requesting_agency)


@router.get("/{case_id}", response_model=CaseOut)
async def get_case(case_id: UUID, current_user: CurrentUser = Depends(get_current_user)):
    case = await case_service.get_case(str(case_id))
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}/status", response_model=CaseOut)
async def update_case_status(
    case_id: UUID,
    payload: CaseStatusUpdate,
    current_user: CurrentUser = Depends(get_current_user),
):
    case = await case_service.update_case_status(str(case_id), payload.status)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.delete("/{case_id}", status_code=204)
async def delete_case(case_id: UUID, current_user: CurrentUser = Depends(require_lab_director)):
    deleted = await case_service.delete_case(str(case_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Case not found")


@router.get("/{case_id}/potential-loss", response_model=PotentialLossOut)
async def get_case_potential_loss(
    case_id: UUID, current_user: CurrentUser = Depends(get_current_user)
):
    loss = await case_service.calculate_potential_loss(str(case_id))
    return PotentialLossOut(
        case_id=case_id,
        potential_loss_usd=float(loss["potential_loss_usd"]),
        potential_loss_sgd=loss["potential_loss_sgd"],
    )


@router.get("/{case_id}/evidence", response_model=list[EvidenceOut])
async def list_case_evidence(case_id: UUID, current_user: CurrentUser = Depends(get_current_user)):
    return await evidence_service.list_evidence_for_case(str(case_id))


@router.post("/{case_id}/evidence", response_model=EvidenceOut)
async def register_case_evidence(
    case_id: UUID,
    payload: EvidenceCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    return await evidence_service.register_evidence_item(
        case_id=str(case_id),
        species_id=str(payload.species_id),
        description=payload.description,
        quantity=payload.quantity,
        unit=payload.unit,
        collection_date=payload.collection_date,
        recorded_by_user_id=current_user.user_id,
        collected_by=payload.collected_by,
    )


@router.get("/{case_id}/suspects", response_model=list[SuspectOut])
async def list_case_suspects(case_id: UUID, current_user: CurrentUser = Depends(get_current_user)):
    return await suspect_service.list_suspects_for_case(str(case_id))


@router.post("/{case_id}/suspects", response_model=SuspectOut)
async def link_case_suspect(
    case_id: UUID,
    payload: SuspectLinkCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    await suspect_service.link_suspect_to_case(
        str(case_id), str(payload.suspect_id), payload.role_in_case
    )
    suspect = await suspect_service.get_suspect(str(payload.suspect_id))
    if suspect is None:
        raise HTTPException(status_code=404, detail="Suspect not found")
    return SuspectOut(**suspect, role_in_case=payload.role_in_case)
