from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.api.v1.auth import get_current_user, get_current_user_optional
from app.schemas.certificate import (
    CertificateIssue,
    CertificateRevoke,
    CertificateSupersede,
    CertificateResponse,
    CertificatePublicResponse,
    CertificateListResponse,
)
from app.services.certificate import (
    issue_certificate,
    revoke_certificate,
    supersede_certificate,
    get_certificate,
    get_certificate_by_token,
    get_certificate_by_number,
    list_certificates,
    get_public_certificate_data,
)
from app.models.user import User
from app.models.certificate import CertificateStatus
from app.core.errors import NotFoundError, ForbiddenError, ValidationError

router = APIRouter(tags=["certificates"])


@router.post("/{application_id}/issue", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
def issue_certificate_endpoint(
    application_id: int,
    issue_data: CertificateIssue,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        certificate = issue_certificate(db, current_user, application_id, issue_data.valid_from, issue_data.valid_until)
        return certificate
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{certificate_id}/revoke", response_model=CertificateResponse)
def revoke_certificate_endpoint(
    certificate_id: int,
    revoke_data: CertificateRevoke,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        certificate = revoke_certificate(db, current_user, certificate_id, revoke_data.reason)
        return certificate
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{certificate_id}/supersede", response_model=CertificateResponse)
def supersede_certificate_endpoint(
    certificate_id: int,
    supersede_data: CertificateSupersede,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        certificate = supersede_certificate(db, current_user, certificate_id, supersede_data.reason, supersede_data.new_certificate_id)
        return certificate
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("", response_model=CertificateListResponse)
def list_certificates_endpoint(
    page: int = 1,
    page_size: int = 20,
    status: Optional[CertificateStatus] = None,
    instrument_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    certificates, total = list_certificates(db, current_user, page, page_size, status, instrument_id)
    return {"items": certificates, "total": total, "page": page, "page_size": page_size}


@router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate_endpoint(
    certificate_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        certificate = get_certificate(db, certificate_id, current_user)
        return certificate
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# Public verification endpoints (no authentication required)
@router.get("/public/verify/{token}", response_model=CertificatePublicResponse)
def verify_certificate_by_token(
    token: str,
    db: Session = Depends(get_db),
):
    data = get_public_certificate_data(db, token)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return data


@router.get("/public/verify", response_model=CertificatePublicResponse)
def verify_certificate_by_id(
    certificate_id: str,
    db: Session = Depends(get_db),
):
    data = get_public_certificate_data(db, certificate_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certificate not found")
    return data