from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from app.models.standards import (
    StandardType, StandardStatus,
    EnforcementCaseType, EnforcementCaseStatus,
)


class StandardBase(BaseModel):
    standard_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    standard_type: StandardType
    nominal_value: str = Field(..., min_length=1, max_length=100)
    unit: str = Field(..., min_length=1, max_length=50)
    accuracy_class: Optional[str] = Field(None, max_length=50)
    manufacturer: Optional[str] = Field(None, max_length=255)
    serial_number: Optional[str] = Field(None, max_length=100)
    calibration_date: Optional[date] = None
    calibration_due_date: Optional[date] = None
    calibration_certificate_number: Optional[str] = Field(None, max_length=100)
    calibration_lab: Optional[str] = Field(None, max_length=255)
    owner_id: Optional[int] = None
    location: Optional[str] = None
    custodian_id: Optional[int] = None
    notes: Optional[str] = None


class StandardCreate(StandardBase):
    pass


class StandardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    nominal_value: Optional[str] = Field(None, min_length=1, max_length=100)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    accuracy_class: Optional[str] = Field(None, max_length=50)
    manufacturer: Optional[str] = Field(None, max_length=255)
    serial_number: Optional[str] = Field(None, max_length=100)
    calibration_date: Optional[date] = None
    calibration_due_date: Optional[date] = None
    calibration_certificate_number: Optional[str] = Field(None, max_length=100)
    calibration_lab: Optional[str] = Field(None, max_length=255)
    calibration_status: Optional[StandardStatus] = None
    owner_id: Optional[int] = None
    location: Optional[str] = None
    custodian_id: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[StandardStatus] = None


class StandardResponse(StandardBase):
    id: int
    calibration_status: StandardStatus
    status: StandardStatus
    created_at: datetime
    updated_at: datetime
    owner: Optional["UserResponse"] = None
    custodian: Optional["UserResponse"] = None

    class Config:
        from_attributes = True


class StandardListResponse(BaseModel):
    items: List[StandardResponse]
    total: int
    page: int
    page_size: int


class StandardUsageCreate(BaseModel):
    standard_id: int
    inspection_id: Optional[int] = None
    application_id: Optional[int] = None
    purpose: Optional[str] = None
    notes: Optional[str] = None


class StandardUsageResponse(BaseModel):
    id: int
    standard_id: int
    inspection_id: Optional[int] = None
    application_id: Optional[int] = None
    used_by_id: int
    used_at: datetime
    purpose: Optional[str] = None
    notes: Optional[str] = None
    standard: Optional[StandardResponse] = None
    used_by: Optional["UserResponse"] = None

    class Config:
        from_attributes = True


class StandardUsageListResponse(BaseModel):
    items: List[StandardUsageResponse]
    total: int
    page: int
    page_size: int


class EnforcementCaseBase(BaseModel):
    case_type: EnforcementCaseType
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    complainant_id: Optional[int] = None
    respondent_id: Optional[int] = None
    instrument_id: Optional[int] = None
    jurisdiction: Optional[str] = Field(None, max_length=255)
    assigned_officer_id: Optional[int] = None
    target_resolution_date: Optional[datetime] = None


class EnforcementCaseCreate(EnforcementCaseBase):
    pass


class EnforcementCaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    case_type: Optional[EnforcementCaseType] = None
    complainant_id: Optional[int] = None
    respondent_id: Optional[int] = None
    instrument_id: Optional[int] = None
    jurisdiction: Optional[str] = Field(None, max_length=255)
    assigned_officer_id: Optional[int] = None
    status: Optional[EnforcementCaseStatus] = None
    target_resolution_date: Optional[datetime] = None
    outcome: Optional[str] = None
    penalty_amount: Optional[int] = None
    penalty_paid: Optional[bool] = None


class EnforcementCaseResponse(EnforcementCaseBase):
    id: int
    case_number: str
    status: EnforcementCaseStatus
    opened_at: datetime
    closed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    penalty_amount: Optional[int] = None
    penalty_paid: bool
    created_at: datetime
    updated_at: datetime
    complainant: Optional["UserResponse"] = None
    respondent: Optional["UserResponse"] = None
    instrument: Optional["InstrumentResponse"] = None
    assigned_officer: Optional["UserResponse"] = None

    class Config:
        from_attributes = True


class EnforcementCaseListResponse(BaseModel):
    items: List[EnforcementCaseResponse]
    total: int
    page: int
    page_size: int


class EnforcementEvidenceCreate(BaseModel):
    case_id: int
    evidence_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    file_path: Optional[str] = Field(None, max_length=500)
    file_hash: Optional[str] = Field(None, max_length=64)
    is_sealed: bool = False
    seal_number: Optional[str] = Field(None, max_length=100)


class EnforcementEvidenceResponse(BaseModel):
    id: int
    case_id: int
    evidence_type: str
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    collected_by_id: int
    collected_at: datetime
    is_sealed: bool
    seal_number: Optional[str] = None
    created_at: datetime
    collector: Optional["UserResponse"] = None

    class Config:
        from_attributes = True


class EnforcementEvidenceListResponse(BaseModel):
    items: List[EnforcementEvidenceResponse]
    total: int
    page: int
    page_size: int


class EnforcementActionCreate(BaseModel):
    case_id: int
    action_type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    performed_by_id: int
    due_date: Optional[datetime] = None
    status: str = "pending"


class EnforcementActionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    action_type: Optional[str] = Field(None, min_length=1, max_length=50)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: Optional[str] = None


class EnforcementActionResponse(BaseModel):
    id: int
    case_id: int
    action_type: str
    title: str
    description: Optional[str] = None
    performed_by_id: int
    performed_at: datetime
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str
    created_at: datetime
    performer: Optional["UserResponse"] = None

    class Config:
        from_attributes = True


class EnforcementActionListResponse(BaseModel):
    items: List[EnforcementActionResponse]
    total: int
    page: int
    page_size: int


class RepairRecordBase(BaseModel):
    instrument_id: int
    application_id: Optional[int] = None
    repair_type: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1)
    performed_by: Optional[str] = Field(None, max_length=255)
    repairer_license: Optional[str] = Field(None, max_length=100)
    repair_date: date
    next_due_date: Optional[date] = None
    old_seal_number: Optional[str] = Field(None, max_length=100)
    new_seal_number: Optional[str] = Field(None, max_length=100)
    seal_broken_reason: Optional[str] = None
    requires_reverification: bool = True
    re_verification_application_id: Optional[int] = None
    cost: Optional[int] = None
    approved_by_id: Optional[int] = None
    work_order_number: Optional[str] = Field(None, max_length=100)
    invoice_number: Optional[str] = Field(None, max_length=100)
    attachment_path: Optional[str] = Field(None, max_length=500)
    attachment_hash: Optional[str] = Field(None, max_length=64)


class RepairRecordCreate(RepairRecordBase):
    pass


class RepairRecordUpdate(BaseModel):
    repair_type: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    performed_by: Optional[str] = Field(None, max_length=255)
    repairer_license: Optional[str] = Field(None, max_length=100)
    repair_date: Optional[date] = None
    next_due_date: Optional[date] = None
    old_seal_number: Optional[str] = Field(None, max_length=100)
    new_seal_number: Optional[str] = Field(None, max_length=100)
    seal_broken_reason: Optional[str] = None
    requires_reverification: Optional[bool] = None
    re_verification_application_id: Optional[int] = None
    cost: Optional[int] = None
    approved_by_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    work_order_number: Optional[str] = Field(None, max_length=100)
    invoice_number: Optional[str] = Field(None, max_length=100)
    attachment_path: Optional[str] = Field(None, max_length=500)
    attachment_hash: Optional[str] = Field(None, max_length=64)
    status: Optional[str] = None


class RepairRecordResponse(RepairRecordBase):
    id: int
    status: str
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    instrument: Optional["InstrumentResponse"] = None
    application: Optional["ApplicationResponse"] = None
    re_verification_application: Optional["ApplicationResponse"] = None
    approver: Optional["UserResponse"] = None

    class Config:
        from_attributes = True


class RepairRecordListResponse(BaseModel):
    items: List[RepairRecordResponse]
    total: int
    page: int
    page_size: int


from app.schemas.user import UserResponse
from app.schemas.instrument import InstrumentResponse
from app.schemas.application import ApplicationResponse

StandardResponse.model_rebuild()
StandardUsageResponse.model_rebuild()
EnforcementCaseResponse.model_rebuild()
EnforcementEvidenceResponse.model_rebuild()
EnforcementActionResponse.model_rebuild()
RepairRecordResponse.model_rebuild()