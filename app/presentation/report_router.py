from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.presentation.security import CurrentUser, get_current_user, require_lab_director
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportOut(BaseModel):
    id: UUID
    month: int
    year: int
    total_seizures: int
    potential_loss_usd: float
    potential_loss_sgd: float
    most_affected_species: str | None
    top_trafficker_nationality: str | None
    status: Literal["draft", "approved"]
    approved_by_user_id: UUID | None
    approved_at: datetime | None
    created_at: datetime


class ReportGenerateRequest(BaseModel):
    year: int
    month: int


class TranslationOut(BaseModel):
    id: UUID
    report_id: UUID
    language: Literal["zh", "ja", "vi"]
    narrative_text: str
    pdf_url: str | None


@router.post("/generate", response_model=ReportOut)
async def generate_report(
    payload: ReportGenerateRequest, current_user: CurrentUser = Depends(get_current_user)
):
    return await report_service.generate_monthly_report(payload.year, payload.month)


@router.get("", response_model=list[ReportOut])
async def list_reports(current_user: CurrentUser = Depends(get_current_user)):
    return await report_service.list_reports()


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(report_id: UUID, current_user: CurrentUser = Depends(get_current_user)):
    report = await report_service.get_report(str(report_id))
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/translations", response_model=list[TranslationOut])
async def list_report_translations(
    report_id: UUID, current_user: CurrentUser = Depends(get_current_user)
):
    return await report_service.list_translations(str(report_id))


@router.patch("/{report_id}/approve", response_model=ReportOut)
async def approve_report(
    report_id: UUID, current_user: CurrentUser = Depends(require_lab_director)
):
    report = await report_service.approve_report(str(report_id), current_user.user_id)
    if report is None:
        raise HTTPException(
            status_code=409, detail="Report not found or is not in draft status"
        )
    return report
