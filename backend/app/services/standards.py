from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.standards import (
    Standard, StandardType, StandardStatus, StandardUsage,
    EnforcementCase, EnforcementCaseType, EnforcementCaseStatus,
    EnforcementEvidence, EnforcementAction,
    RepairRecord
)
from app.models.user import User, UserRole
from app.models.instrument import Instrument
from app.models.application import Application
from app.models.inspection import Inspection
from app.core.errors import NotFoundError, ForbiddenError, ValidationError, ConflictError
from app.core.permissions import has_permission, Permission, can_access_application
from app.services.audit import create_audit_event


# ============================================================================
# Standards Registry
# ============================================================================

def create_standard(
    db: Session,
    actor: User,
    standard_code: str,
    name: str,
    standard_type: StandardType,
    nominal_value: str,
    unit: str,
    accuracy_class: Optional[str] = None,
    manufacturer: Optional[str] = None,
    serial_number: Optional[str] = None,
    calibration_date: Optional[date] = None,
    calibration_due_date: Optional[date] = None,
    calibration_certificate_number: Optional[str] = None,
    calibration_lab: Optional[str] = None,
    owner_id: Optional[int] = None,
    location: Optional[str] = None,
    custodian_id: Optional[int] = None,
    notes: Optional[str] = None,
) -> Standard:
    if not has_permission(actor, Permission.CONFIG_MANAGE):
        raise ForbiddenError("Not authorized to create standards")

    existing = db.query(Standard).filter(Standard.standard_code == standard_code).first()
    if existing:
        raise ConflictError("Standard with this code already exists")

    standard = Standard(
        standard_code=standard_code,
        name=name,
        standard_type=standard_type,
        nominal_value=nominal_value,
        unit=unit,
        accuracy_class=accuracy_class,
        manufacturer=manufacturer,
        serial_number=serial_number,
        calibration_date=calibration_date,
        calibration_due_date=calibration_due_date,
        calibration_certificate_number=calibration_certificate_number,
        calibration_lab=calibration_lab,
        owner_id=owner_id,
        location=location,
        custodian_id=custodian_id,
        notes=notes,
    )
    db.add(standard)
    db.commit()
    db.refresh(standard)

    create_audit_event(
        db, actor.id, "create_standard", "standard", standard.id,
        new_status=StandardStatus.ACTIVE.value, reason=f"Standard {standard_code} created"
    )
    return standard


def get_standard(db: Session, standard_id: int, user: User) -> Standard:
    standard = db.query(Standard).filter(Standard.id == standard_id).first()
    if not standard:
        raise NotFoundError("Standard", standard_id)
    # Admin/Regulator can view all; owner/custodian can view their own
    if user.role not in [UserRole.ADMIN, UserRole.REGULATOR]:
        if standard.owner_id != user.id and standard.custodian_id != user.id:
            raise ForbiddenError()
    return standard


def list_standards(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    standard_type: Optional[StandardType] = None,
    status: Optional[StandardStatus] = None,
    calibration_overdue: bool = False,
    search: Optional[str] = None,
) -> Tuple[List[Standard], int]:
    query = db.query(Standard)

    if user.role not in [UserRole.ADMIN, UserRole.REGULATOR]:
        query = query.filter(
            or_(Standard.owner_id == user.id, Standard.custodian_id == user.id)
        )

    if standard_type:
        query = query.filter(Standard.standard_type == standard_type)
    if status:
        query = query.filter(Standard.status == status)
    if calibration_overdue:
        query = query.filter(
            and_(
                Standard.calibration_due_date < date.today(),
                Standard.calibration_status.in_([StandardStatus.ACTIVE, StandardStatus.EXPIRED])
            )
        )
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Standard.standard_code.ilike(search_term),
                Standard.name.ilike(search_term),
                Standard.serial_number.ilike(search_term),
            )
        )

    total = query.count()
    standards = query.order_by(Standard.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return standards, total


def update_standard(
    db: Session,
    standard_id: int,
    actor: User,
    **kwargs,
) -> Standard:
    standard = get_standard(db, standard_id, actor)
    if actor.role not in [UserRole.ADMIN, UserRole.REGULATOR]:
        if standard.owner_id != actor.id and standard.custodian_id != actor.id:
            raise ForbiddenError()

    for key, value in kwargs.items():
        if value is not None and hasattr(standard, key):
            setattr(standard, key, value)

    standard.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(standard)

    create_audit_event(
        db, actor.id, "update_standard", "standard", standard.id,
        reason="Standard updated"
    )
    return standard


def record_standard_usage(
    db: Session,
    user: User,
    standard_id: int,
    inspection_id: Optional[int] = None,
    application_id: Optional[int] = None,
    purpose: Optional[str] = None,
    notes: Optional[str] = None,
) -> StandardUsage:
    standard = db.query(Standard).filter(Standard.id == standard_id).first()
    if not standard:
        raise NotFoundError("Standard", standard_id)

    # Check if standard is valid for use
    if standard.calibration_status != StandardStatus.ACTIVE:
        raise ValidationError(f"Standard is not active for use (status: {standard.calibration_status.value})")
    if standard.calibration_due_date and standard.calibration_due_date < date.today():
        raise ValidationError("Standard calibration has expired")

    usage = StandardUsage(
        standard_id=standard_id,
        inspection_id=inspection_id,
        application_id=application_id,
        used_by_id=user.id,
        purpose=purpose,
        notes=notes,
    )
    db.add(usage)
    db.commit()
    db.refresh(usage)

    create_audit_event(
        db, user.id, "use_standard", "standard_usage", usage.id,
        new_status="used", reason=purpose
    )
    return usage


def list_standard_usages(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    standard_id: Optional[int] = None,
) -> Tuple[List[StandardUsage], int]:
    query = db.query(StandardUsage).join(Standard)

    if user.role not in [UserRole.ADMIN, UserRole.REGULATOR]:
        query = query.filter(
            or_(Standard.owner_id == user.id, Standard.custodian_id == user.id)
        )

    if standard_id:
        query = query.filter(StandardUsage.standard_id == standard_id)

    total = query.count()
    usages = query.order_by(StandardUsage.used_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return usages, total


def get_overdue_standards(db: Session) -> List[Standard]:
    """Get all standards with expired or expiring calibration."""
    now = date.today()
    thirty_days = now + timedelta(days=30)
    return db.query(Standard).filter(
        and_(
            Standard.calibration_due_date <= thirty_days,
            Standard.calibration_status.in_([StandardStatus.ACTIVE, StandardStatus.EXPIRED])
        )
    ).all()


# ============================================================================
# Enforcement Cases
# ============================================================================

def create_enforcement_case(
    db: Session,
    actor: User,
    case_type: EnforcementCaseType,
    title: str,
    description: Optional[str] = None,
    complainant_id: Optional[int] = None,
    respondent_id: Optional[int] = None,
    instrument_id: Optional[int] = None,
    jurisdiction: Optional[str] = None,
    assigned_officer_id: Optional[int] = None,
    target_resolution_date: Optional[datetime] = None,
) -> EnforcementCase:
    if not has_permission(actor, Permission.CONFIG_MANAGE) and actor.role not in [UserRole.LMO, UserRole.REGULATOR, UserRole.ADMIN]:
        raise ForbiddenError("Not authorized to create enforcement cases")

    import uuid
    case_number = f"ENF-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    case = EnforcementCase(
        case_number=case_number,
        case_type=case_type,
        title=title,
        description=description,
        complainant_id=complainant_id or actor.id,
        respondent_id=respondent_id,
        instrument_id=instrument_id,
        jurisdiction=jurisdiction,
        assigned_officer_id=assigned_officer_id,
        target_resolution_date=target_resolution_date,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    create_audit_event(
        db, actor.id, "create_enforcement_case", "enforcement_case", case.id,
        new_status=EnforcementCaseStatus.OPEN.value, reason=f"Case {case_number} created"
    )
    return case


def get_enforcement_case(db: Session, case_id: int, user: User) -> EnforcementCase:
    case = db.query(EnforcementCase).filter(EnforcementCase.id == case_id).first()
    if not case:
        raise NotFoundError("EnforcementCase", case_id)

    if user.role == UserRole.LMO:
        if case.assigned_officer_id != user.id:
            raise ForbiddenError()
    elif user.role == UserRole.GATC:
        raise ForbiddenError()
    elif user.role == UserRole.OWNER:
        if case.complainant_id != user.id and case.respondent_id != user.id:
            raise ForbiddenError()

    return case


def list_enforcement_cases(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status: Optional[EnforcementCaseStatus] = None,
    case_type: Optional[EnforcementCaseType] = None,
    assigned_officer_id: Optional[int] = None,
    jurisdiction: Optional[str] = None,
) -> Tuple[List[EnforcementCase], int]:
    query = db.query(EnforcementCase)

    if user.role == UserRole.OWNER:
        query = query.filter(
            or_(
                EnforcementCase.complainant_id == user.id,
                EnforcementCase.respondent_id == user.id,
            )
        )
    elif user.role == UserRole.LMO:
        query = query.filter(EnforcementCase.assigned_officer_id == user.id)
    elif user.role == UserRole.GATC:
        query = query.filter(False)  # GATC doesn't see enforcement cases by default

    if status:
        query = query.filter(EnforcementCase.status == status)
    if case_type:
        query = query.filter(EnforcementCase.case_type == case_type)
    if assigned_officer_id:
        query = query.filter(EnforcementCase.assigned_officer_id == assigned_officer_id)
    if jurisdiction:
        query = query.filter(EnforcementCase.jurisdiction == jurisdiction)

    total = query.count()
    cases = query.order_by(EnforcementCase.opened_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return cases, total


def update_enforcement_case(
    db: Session,
    case_id: int,
    actor: User,
    **kwargs,
) -> EnforcementCase:
    case = get_enforcement_case(db, case_id, actor)

    if actor.role == UserRole.LMO and case.assigned_officer_id != actor.id:
        raise ForbiddenError("Not assigned to this case")

    old_status = case.status

    for key, value in kwargs.items():
        if value is not None and hasattr(case, key):
            setattr(case, key, value)

    if "status" in kwargs and kwargs["status"] != old_status:
        if kwargs["status"] in [EnforcementCaseStatus.CLOSED, EnforcementCaseStatus.DISMISSED]:
            case.closed_at = datetime.utcnow()

    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)

    create_audit_event(
        db, actor.id, "update_enforcement_case", "enforcement_case", case.id,
        previous_status=old_status.value if old_status else None,
        new_status=case.status.value,
        reason="Enforcement case updated"
    )
    return case


def add_enforcement_evidence(
    db: Session,
    actor: User,
    case_id: int,
    evidence_type: str,
    title: str,
    description: Optional[str] = None,
    file_path: Optional[str] = None,
    file_hash: Optional[str] = None,
    is_sealed: bool = False,
    seal_number: Optional[str] = None,
) -> EnforcementEvidence:
    case = get_enforcement_case(db, case_id, actor)

    if actor.role == UserRole.LMO and case.assigned_officer_id != actor.id:
        raise ForbiddenError("Not assigned to this case")

    evidence = EnforcementEvidence(
        case_id=case_id,
        evidence_type=evidence_type,
        title=title,
        description=description,
        file_path=file_path,
        file_hash=file_hash,
        collected_by_id=actor.id,
        is_sealed=is_sealed,
        seal_number=seal_number,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    create_audit_event(
        db, actor.id, "add_enforcement_evidence", "enforcement_evidence", evidence.id,
        new_status=evidence_type, reason=title
    )
    return evidence


def add_enforcement_action(
    db: Session,
    actor: User,
    case_id: int,
    action_type: str,
    title: str,
    description: Optional[str] = None,
    due_date: Optional[datetime] = None,
) -> EnforcementAction:
    case = get_enforcement_case(db, case_id, actor)

    if actor.role == UserRole.LMO and case.assigned_officer_id != actor.id:
        raise ForbiddenError("Not assigned to this case")

    action = EnforcementAction(
        case_id=case_id,
        action_type=action_type,
        title=title,
        description=description,
        performed_by_id=actor.id,
        due_date=due_date,
        status="pending",
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    create_audit_event(
        db, actor.id, "add_enforcement_action", "enforcement_action", action.id,
        new_status="pending", reason=title
    )
    return action


# ============================================================================
# Repair/Tamper Records
# ============================================================================

def create_repair_record(
    db: Session,
    actor: User,
    instrument_id: int,
    repair_type: str,
    description: str,
    performed_by: Optional[str] = None,
    repairer_license: Optional[str] = None,
    repair_date: date = None,
    next_due_date: Optional[date] = None,
    old_seal_number: Optional[str] = None,
    new_seal_number: Optional[str] = None,
    seal_broken_reason: Optional[str] = None,
    requires_reverification: bool = True,
    re_verification_application_id: Optional[int] = None,
    cost: Optional[int] = None,
    approved_by_id: Optional[int] = None,
    work_order_number: Optional[str] = None,
    invoice_number: Optional[str] = None,
    attachment_path: Optional[str] = None,
    attachment_hash: Optional[str] = None,
) -> RepairRecord:
    if not has_permission(actor, Permission.INSTRUMENT_CREATE) and actor.role not in [UserRole.LMO, UserRole.REGULATOR, UserRole.ADMIN]:
        raise ForbiddenError("Not authorized to create repair records")

    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    if repair_date is None:
        repair_date = date.today()

    repair = RepairRecord(
        instrument_id=instrument_id,
        repair_type=repair_type,
        description=description,
        performed_by=performed_by,
        repairer_license=repairer_license,
        repair_date=repair_date,
        next_due_date=next_due_date,
        old_seal_number=old_seal_number,
        new_seal_number=new_seal_number,
        seal_broken_reason=seal_broken_reason,
        requires_reverification=requires_reverification,
        re_verification_application_id=re_verification_application_id,
        cost=cost,
        approved_by_id=approved_by_id,
        approved_at=datetime.utcnow() if approved_by_id else None,
        work_order_number=work_order_number,
        invoice_number=invoice_number,
        attachment_path=attachment_path,
        attachment_hash=attachment_hash,
    )
    db.add(repair)
    db.commit()
    db.refresh(repair)

    # If seal was broken, flag instrument for re-verification
    if old_seal_number and new_seal_number:
        instrument.status = "under_verification"
        db.commit()

    create_audit_event(
        db, actor.id, "create_repair_record", "repair_record", repair.id,
        new_status="created", reason=f"Repair type: {repair_type}, seal replaced: {bool(old_seal_number)}"
    )
    return repair


def get_repair_record(db: Session, repair_id: int, user: User) -> RepairRecord:
    repair = db.query(RepairRecord).filter(RepairRecord.id == repair_id).first()
    if not repair:
        raise NotFoundError("RepairRecord", repair_id)

    if user.role == UserRole.OWNER:
        instrument = db.query(Instrument).filter(Instrument.id == repair.instrument_id).first()
        if instrument.owner_id != user.id:
            raise ForbiddenError()
    elif user.role == UserRole.LMO:
        # LMO can view repairs in their jurisdiction
        instrument = db.query(Instrument).filter(Instrument.id == repair.instrument_id).first()
        # Could add jurisdiction check here

    return repair


def list_repair_records(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    instrument_id: Optional[int] = None,
    repair_type: Optional[str] = None,
    seal_broken: Optional[bool] = None,
) -> Tuple[List[RepairRecord], int]:
    query = db.query(RepairRecord).join(Instrument)

    if user.role == UserRole.OWNER:
        query = query.filter(Instrument.owner_id == user.id)
    elif user.role == UserRole.LMO:
        if user.jurisdiction:
            query = query.filter(Instrument.jurisdiction == user.jurisdiction)

    if instrument_id:
        query = query.filter(RepairRecord.instrument_id == instrument_id)
    if repair_type:
        query = query.filter(RepairRecord.repair_type == repair_type)
    if seal_broken is not None:
        if seal_broken:
            query = query.filter(RepairRecord.old_seal_number.isnot(None))
        else:
            query = query.filter(RepairRecord.old_seal_number.is_(None))

    total = query.count()
    repairs = query.order_by(RepairRecord.repair_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return repairs, total


def update_repair_record(
    db: Session,
    repair_id: int,
    actor: User,
    **kwargs,
) -> RepairRecord:
    repair = get_repair_record(db, repair_id, actor)

    if actor.role == UserRole.OWNER:
        raise ForbiddenError("Owners cannot modify repair records")

    for key, value in kwargs.items():
        if value is not None and hasattr(repair, key):
            setattr(repair, key, value)

    if "approved_by_id" in kwargs and kwargs["approved_by_id"]:
        repair.approved_at = datetime.utcnow()

    repair.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(repair)

    create_audit_event(
        db, actor.id, "update_repair_record", "repair_record", repair.id,
        reason="Repair record updated"
    )
    return repair