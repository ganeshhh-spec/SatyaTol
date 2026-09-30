from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.application import VerificationType, ApplicationStatus


class ApplicationBase(BaseModel):
    instrument_id: int
    verification_type: VerificationType
    jurisdiction: Optional[str] = None
    requested_appointment: Optional[datetime] = None
    remarks: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    jurisdiction: Optional[str] = None
    requested_appointment: Optional[datetime] = None
    remarks: Optional[str] = None
    assigned_officer_id: Optional[int] = None
    assigned_centre_id: Optional[int] = None
    fee_amount: Optional[int] = None
    fee_paid: Optional[bool] = None


class ApplicationSubmit(BaseModel):
    pass


class ApplicationReview(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|request_correction)$")
    reason: Optional[str] = None


class ApplicationSchedule(BaseModel):
    assigned_officer_id: Optional[int] = None
    assigned_centre_id: Optional[int] = None
    scheduled_start: datetime
    scheduled_end: datetime
    location: Optional[str] = None
    mode: Optional[str] = None


class ApplicationResponse(ApplicationBase):
    id: int
    applicant_id: int
    status: ApplicationStatus
    assigned_officer_id: Optional[int] = None
    assigned_centre_id: Optional[int] = None
    fee_amount: Optional[int] = None
    fee_paid: bool
    submitted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    total: int
    page: int
    page_size: int


class ApplicationDetailResponse(ApplicationResponse):
    instrument: Optional["InstrumentResponse"] = None
    applicant: Optional["UserResponse"] = None
    assigned_officer: Optional["UserResponse"] = None
    assigned_centre: Optional["UserResponse"] = None
    attachments: List["AttachmentResponse"] = []
    appointments: List["AppointmentResponse"] = []
    inspections: List["InspectionResponse"] = []
    certificates: List["CertificateResponse"] = []


from app.schemas.instrument import InstrumentResponse
from app.schemas.user import UserResponse
from app.schemas.attachment import AttachmentResponse
from app.schemas.appointment import AppointmentResponse
from app.schemas.inspection import InspectionResponse
from app.schemas.certificate import CertificateResponse

ApplicationDetailResponse.model_rebuild()