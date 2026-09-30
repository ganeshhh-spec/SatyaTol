from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.certificate import CertificateStatus


class CertificateBase(BaseModel):
    pass


class CertificateIssue(BaseModel):
    valid_from: datetime
    valid_until: datetime


class CertificateRevoke(BaseModel):
    reason: str = Field(..., min_length=1)


class CertificateSupersede(BaseModel):
    reason: str = Field(..., min_length=1)
    new_certificate_id: int


class CertificateResponse(BaseModel):
    id: int
    application_id: int
    instrument_id: int
    certificate_number: str
    verification_token: str
    issue_date: datetime
    valid_from: datetime
    valid_until: datetime
    status: CertificateStatus
    issuer_id: int
    revocation_reason: Optional[str] = None
    revoked_at: Optional[datetime] = None
    superseded_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    instrument: Optional["InstrumentResponse"] = None
    issuer: Optional["UserResponse"] = None

    class Config:
        from_attributes = True


class CertificatePublicResponse(BaseModel):
    certificate_id: str
    certificate_number: str
    instrument_category: str
    manufacturer: str
    model: str
    serial_number_masked: str
    issue_date: datetime
    valid_from: datetime
    valid_until: datetime
    status: str
    issuing_authority: str
    issuing_office: str
    verified_at: datetime
    is_prototype: bool = True


class CertificateListResponse(BaseModel):
    items: list[CertificateResponse]
    total: int
    page: int
    page_size: int


from app.schemas.instrument import InstrumentResponse
from app.schemas.user import UserResponse
CertificateResponse.model_rebuild()