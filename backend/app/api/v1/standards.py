from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.schemas.standards import (
    StandardCreate, StandardUpdate, StandardResponse, StandardListResponse,
    StandardUsageCreate, StandardUsageResponse, StandardUsageListResponse,
    EnforcementCaseCreate, EnforcementCaseUpdate, EnforcementCaseResponse, EnforcementCaseListResponse,
    EnforcementEvidenceCreate, EnforcementEvidenceResponse, EnforcementEvidenceListResponse,
    EnforcementActionCreate, EnforcementActionUpdate, EnforcementActionResponse, EnforcementActionListResponse,
    RepairRecordCreate, RepairRecordUpdate, RepairRecordResponse, RepairRecordListResponse,
)
from app.services.standards import (
    create_standard, get_standard, list_standards, update_standard,
    record_standard_usage, list_standard_usages, get_overdue_standards,
    create_enforcement_case, get_enforcement_case, list_enforcement_cases, update_enforcement_case,
    add_enforcement_evidence, add_enforcement_action,
    create_repair_record, get_repair_record, list_repair_records, update_repair_record,
)
from app.models.user import User
from app.models.standards import StandardType, StandardStatus, EnforcementCaseType, EnforcementCaseStatus
from app.core.errors import NotFoundError, ForbiddenError, ValidationError, ConflictError

router = APIRouter(tags=["standards"])


# ============================================================================
# Standards Registry
# ============================================================================

@router.post("/standards", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
def create_standard_endpoint(
    standard_data: StandardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        standard = create_standard(db, current_user, **standard_data.model_dump())
        return standard
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/standards", response_model=StandardListResponse)
def list_standards_endpoint(
    page: int = 1,
    page_size: int = 20,
    standard_type: Optional[StandardType] = None,
    status: Optional[StandardStatus] = None,
    calibration_overdue: bool = False,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    standards, total = list_standards(db, current_user, page, page_size, standard_type, status, calibration_overdue, search)
    return {"items": standards, "total": total, "page": page, "page_size": page_size}


@router.get("/standards/overdue", response_model=StandardListResponse)
def get_overdue_standards_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.standards import get_overdue_standards
    standards = get_overdue_standards(db)
    return {"items": standards, "total": len(standards), "page": 1, "page_size": len(standards)}


@router.get("/standards/{standard_id}", response_model=StandardResponse)
def get_standard_endpoint(
    standard_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        standard = get_standard(db, standard_id, current_user)
        return standard
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/standards/{standard_id}", response_model=StandardResponse)
def update_standard_endpoint(
    standard_id: int,
    standard_data: StandardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        update_data = {k: v for k, v in standard_data.model_dump().items() if v is not None}
        standard = update_standard(db, standard_id, current_user, **update_data)
        return standard
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/standards/{standard_id}/usage", response_model=StandardUsageResponse, status_code=status.HTTP_201_CREATED)
def record_standard_usage_endpoint(
    standard_id: int,
    usage_data: StandardUsageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        usage = record_standard_usage(db, current_user, standard_id, **usage_data.model_dump(exclude={"standard_id"}))
        return usage
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/standards/{standard_id}/usages", response_model=StandardUsageListResponse)
def list_standard_usages_endpoint(
    standard_id: int,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    usages, total = list_standard_usages(db, current_user, page, page_size, standard_id)
    return {"items": usages, "total": total, "page": page, "page_size": page_size}


# ============================================================================
# Enforcement Cases
# ============================================================================

@router.post("/enforcement/cases", response_model=EnforcementCaseResponse, status_code=status.HTTP_201_CREATED)
def create_enforcement_case_endpoint(
    case_data: EnforcementCaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        case = create_enforcement_case(db, current_user, **case_data.model_dump())
        return case
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/enforcement/cases", response_model=EnforcementCaseListResponse)
def list_enforcement_cases_endpoint(
    page: int = 1,
    page_size: int = 20,
    status: Optional[EnforcementCaseStatus] = None,
    case_type: Optional[EnforcementCaseType] = None,
    assigned_officer_id: Optional[int] = None,
    jurisdiction: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cases, total = list_enforcement_cases(db, current_user, page, page_size, status, case_type, assigned_officer_id, jurisdiction)
    return {"items": cases, "total": total, "page": page, "page_size": page_size}


@router.get("/enforcement/cases/{case_id}", response_model=EnforcementCaseResponse)
def get_enforcement_case_endpoint(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        case = get_enforcement_case(db, case_id, current_user)
        return case
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/enforcement/cases/{case_id}", response_model=EnforcementCaseResponse)
def update_enforcement_case_endpoint(
    case_id: int,
    case_data: EnforcementCaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        update_data = {k: v for k, v in case_data.model_dump().items() if v is not None}
        case = update_enforcement_case(db, case_id, current_user, **update_data)
        return case
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/enforcement/cases/{case_id}/evidence", response_model=EnforcementEvidenceResponse, status_code=status.HTTP_201_CREATED)
def add_enforcement_evidence_endpoint(
    case_id: int,
    evidence_data: EnforcementEvidenceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        evidence = add_enforcement_evidence(db, current_user, case_id, **evidence_data.model_dump(exclude={"case_id"}))
        return evidence
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/enforcement/cases/{case_id}/actions", response_model=EnforcementActionResponse, status_code=status.HTTP_201_CREATED)
def add_enforcement_action_endpoint(
    case_id: int,
    action_data: EnforcementActionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        action = add_enforcement_action(db, current_user, case_id, **action_data.model_dump(exclude={"case_id"}))
        return action
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# ============================================================================
# Repair/Tamper Records
# ============================================================================

@router.post("/repairs", response_model=RepairRecordResponse, status_code=status.HTTP_201_CREATED)
def create_repair_record_endpoint(
    repair_data: RepairRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        repair = create_repair_record(db, current_user, **repair_data.model_dump())
        return repair
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("/repairs", response_model=RepairRecordListResponse)
def list_repair_records_endpoint(
    page: int = 1,
    page_size: int = 20,
    instrument_id: Optional[int] = None,
    repair_type: Optional[str] = None,
    seal_broken: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repairs, total = list_repair_records(db, current_user, page, page_size, instrument_id, repair_type, seal_broken)
    return {"items": repairs, "total": total, "page": page, "page_size": page_size}


@router.get("/repairs/{repair_id}", response_model=RepairRecordResponse)
def get_repair_record_endpoint(
    repair_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        repair = get_repair_record(db, repair_id, current_user)
        return repair
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/repairs/{repair_id}", response_model=RepairRecordResponse)
def update_repair_record_endpoint(
    repair_id: int,
    repair_data: RepairRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        update_data = {k: v for k, v in repair_data.model_dump().items() if v is not None}
        repair = update_repair_record(db, repair_id, current_user, **update_data)
        return repair
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))