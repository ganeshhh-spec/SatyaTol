from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.schemas.instrument import InstrumentListResponse
from app.schemas.application import ApplicationListResponse
from app.schemas.certificate import CertificateListResponse
from app.services.search import search_instruments, search_applications, search_certificates
from app.models.user import User
from app.models.instrument import InstrumentCategory, InstrumentStatus
from app.models.application import ApplicationStatus, VerificationType
from app.models.certificate import CertificateStatus

router = APIRouter(tags=["search"])


@router.get("/instruments", response_model=InstrumentListResponse)
def search_instruments_endpoint(
    q: Optional[str] = None,
    category: Optional[InstrumentCategory] = None,
    status: Optional[InstrumentStatus] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        instruments, total = search_instruments(db, current_user, q, category, status, page, page_size)
        return {"items": instruments, "total": total, "page": page, "page_size": page_size}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/applications", response_model=ApplicationListResponse)
def search_applications_endpoint(
    q: Optional[str] = None,
    status: Optional[ApplicationStatus] = None,
    verification_type: Optional[VerificationType] = None,
    instrument_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        applications, total = search_applications(db, current_user, q, status, verification_type, instrument_id, page, page_size)
        return {"items": applications, "total": total, "page": page, "page_size": page_size}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/certificates", response_model=CertificateListResponse)
def search_certificates_endpoint(
    q: Optional[str] = None,
    status: Optional[CertificateStatus] = None,
    instrument_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        certificates, total = search_certificates(db, current_user, q, status, instrument_id, page, page_size)
        return {"items": certificates, "total": total, "page": page, "page_size": page_size}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))