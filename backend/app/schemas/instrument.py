from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from app.models.instrument import InstrumentCategory, InstrumentStatus
from app.models.application import ApplicationStatus
from app.models.appointment import AppointmentStatus
from app.models.inspection import InspectionResult
from app.models.certificate import CertificateStatus
from app.models.audit import AuditEvent


class InstrumentBase(BaseModel):
    category: InstrumentCategory
    instrument_type: str = Field(..., min_length=1, max_length=100)
    manufacturer: str = Field(..., min_length=1, max_length=255)
    model: str = Field(..., min_length=1, max_length=100)
    serial_number: str = Field(..., min_length=1, max_length=100)
    capacity: Optional[str] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    use_context: Optional[str] = None


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentUpdate(BaseModel):
    category: Optional[InstrumentCategory] = None
    instrument_type: Optional[str] = Field(None, min_length=1, max_length=100)
    manufacturer: Optional[str] = Field(None, min_length=1, max_length=255)
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    serial_number: Optional[str] = Field(None, min_length=1, max_length=100)
    capacity: Optional[str] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    use_context: Optional[str] = None
    status: Optional[InstrumentStatus] = None


class InstrumentResponse(InstrumentBase):
    id: int
    owner_id: int
    registration_date: datetime
    status: InstrumentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InstrumentListResponse(BaseModel):
    items: list[InstrumentResponse]
    total: int
    page: int
    page_size: int


class InstrumentTimelineEvent(BaseModel):
    date: Optional[datetime] = None
    type: str
    title: str
    details: str
    entity_type: str
    entity_id: int


class InstrumentHistoryResponse(BaseModel):
    instrument: InstrumentResponse
    applications: List[Any] = []
    appointments: List[Any] = []
    inspections: List[Any] = []
    certificates: List[Any] = []
    audit_events: List[Any] = []
    timeline: List[InstrumentTimelineEvent] = []