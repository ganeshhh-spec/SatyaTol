from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.inspection import InspectionResult


class InspectionBase(BaseModel):
    observations: Optional[str] = None
    checklist: Optional[str] = None
    condition_notes: Optional[str] = None
    result: InspectionResult
    photos: Optional[str] = None
    signature_metadata: Optional[str] = None


class InspectionCreate(InspectionBase):
    application_id: int
    appointment_id: Optional[int] = None
    is_finalized: bool = False


class InspectionUpdate(BaseModel):
    observations: Optional[str] = None
    checklist: Optional[str] = None
    condition_notes: Optional[str] = None
    result: Optional[InspectionResult] = None
    photos: Optional[str] = None
    signature_metadata: Optional[str] = None
    is_finalized: Optional[bool] = None


class InspectionFinalize(BaseModel):
    result: Optional[InspectionResult] = None
    observations: Optional[str] = None
    checklist: Optional[str] = None
    condition_notes: Optional[str] = None


class InspectionResponse(InspectionBase):
    id: int
    application_id: int
    inspector_id: int
    appointment_id: Optional[int] = None
    inspection_date: datetime
    is_finalized: bool
    created_at: datetime
    updated_at: datetime
    inspector: Optional["UserResponse"] = None

    class Config:
        from_attributes = True


class InspectionListResponse(BaseModel):
    items: list[InspectionResponse]
    total: int
    page: int
    page_size: int


from app.schemas.user import UserResponse
InspectionResponse.model_rebuild()