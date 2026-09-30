from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.appointment import AppointmentStatus


class AppointmentBase(BaseModel):
    scheduled_start: datetime
    scheduled_end: datetime
    location: Optional[str] = None
    mode: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    application_id: int
    assigned_officer_id: Optional[int] = None
    assigned_centre_id: Optional[int] = None


class AppointmentUpdate(BaseModel):
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    location: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    id: int
    application_id: int
    assigned_officer_id: Optional[int] = None
    assigned_centre_id: Optional[int] = None
    status: AppointmentStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    assigned_officer: Optional["UserResponse"] = None
    assigned_centre: Optional["UserResponse"] = None

    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    items: list[AppointmentResponse]
    total: int
    page: int
    page_size: int


from app.schemas.user import UserResponse
AppointmentResponse.model_rebuild()