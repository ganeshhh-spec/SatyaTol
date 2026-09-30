from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.inspection import Inspection, InspectionResult
from app.models.application import Application, ApplicationStatus
from app.models.appointment import Appointment
from app.models.user import User, UserRole
from app.core.errors import NotFoundError, ForbiddenError, ValidationError
from app.core.permissions import can_access_inspection, has_permission, Permission
from app.services.audit import create_audit_event


def create_inspection(
    db: Session,
    inspector: User,
    application_id: int,
    appointment_id: Optional[int],
    result: InspectionResult,
    observations: Optional[str] = None,
    checklist: Optional[str] = None,
    condition_notes: Optional[str] = None,
    photos: Optional[str] = None,
    signature_metadata: Optional[str] = None,
    is_finalized: bool = False,
) -> Inspection:
    if not has_permission(inspector, Permission.INSPECTION_CREATE):
        raise ForbiddenError("Not authorized to create inspections")

    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise NotFoundError("Application", application_id)

    # Check if inspector is assigned to this application
    if application.assigned_officer_id != inspector.id and application.assigned_centre_id != inspector.id:
        raise ForbiddenError("Inspector is not assigned to this application")

    if application.status not in [ApplicationStatus.SCHEDULED, ApplicationStatus.INSPECTION_IN_PROGRESS]:
        raise ValidationError("Application is not in a state that allows inspection")

    if appointment_id:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise NotFoundError("Appointment", appointment_id)
        if appointment.application_id != application_id:
            raise ValidationError("Appointment does not belong to this application")

    existing_finalized = (
        db.query(Inspection)
        .filter(Inspection.application_id == application_id, Inspection.is_finalized == True)
        .first()
    )
    if existing_finalized:
        raise ValidationError("A finalized inspection already exists for this application")

    if is_finalized:
        if not observations or not observations.strip():
            raise ValidationError("Observations are required to finalize inspection")
        if result in [InspectionResult.FAIL, InspectionResult.NEEDS_FOLLOW_UP]:
            if not condition_notes or not condition_notes.strip():
                raise ValidationError("Condition notes/reason required for fail or needs_follow_up result")

    inspection = Inspection(
        application_id=application_id,
        inspector_id=inspector.id,
        appointment_id=appointment_id,
        inspection_date=datetime.utcnow(),
        result=result,
        observations=observations,
        checklist=checklist,
        condition_notes=condition_notes,
        photos=photos,
        signature_metadata=signature_metadata,
        is_finalized=is_finalized,
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)

    if is_finalized:
        from app.services.application import transition_application_status
        transition_application_status(db, application, ApplicationStatus.INSPECTION_RECORDED, inspector, "Inspection recorded")
        create_audit_event(
            db, inspector.id, "create_inspection", "inspection", inspection.id,
            new_status=result.value, reason=observations
        )
    else:
        create_audit_event(
            db, inspector.id, "create_inspection_draft", "inspection", inspection.id,
            new_status="draft", reason=observations
        )
    return inspection


def get_inspection(db: Session, inspection_id: int, user: User) -> Inspection:
    inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
    if not inspection:
        raise NotFoundError("Inspection", inspection_id)
    application = db.query(Application).filter(Application.id == inspection.application_id).first()
    jurisdiction = application.jurisdiction if application else None
    if not can_access_inspection(user, inspection.inspector_id, jurisdiction):
        raise ForbiddenError()
    return inspection


def list_inspections(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    result: Optional[InspectionResult] = None,
) -> Tuple[List[Inspection], int]:
    query = db.query(Inspection).join(Application)

    if user.role == UserRole.LMO:
        query = query.filter(Inspection.inspector_id == user.id)
        if user.jurisdiction:
            query = query.filter(Application.jurisdiction == user.jurisdiction)
    elif user.role == UserRole.GATC:
        query = query.filter(Inspection.inspector_id == user.id)

    if result:
        query = query.filter(Inspection.result == result)

    total = query.count()
    inspections = query.order_by(Inspection.inspection_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return inspections, total


def finalize_inspection(
    db: Session,
    inspection_id: int,
    inspector: User,
    result: Optional[InspectionResult] = None,
    observations: Optional[str] = None,
    checklist: Optional[str] = None,
    condition_notes: Optional[str] = None,
) -> Inspection:
    inspection = get_inspection(db, inspection_id, inspector)

    if inspection.is_finalized:
        raise ValidationError("Inspection is already finalized")

    if not has_permission(inspector, Permission.INSPECTION_CREATE):
        raise ForbiddenError("Not authorized to finalize inspections")

    application = db.query(Application).filter(Application.id == inspection.application_id).first()
    if not application:
        raise NotFoundError("Application", inspection.application_id)

    if application.status not in [ApplicationStatus.SCHEDULED, ApplicationStatus.INSPECTION_IN_PROGRESS, ApplicationStatus.INSPECTION_RECORDED]:
        raise ValidationError("Application is not in a state that allows inspection finalization")

    final_result = result or inspection.result
    final_observations = observations or inspection.observations
    final_condition_notes = condition_notes or inspection.condition_notes

    if not final_observations or not final_observations.strip():
        raise ValidationError("Observations are required to finalize inspection")

    if final_result in [InspectionResult.FAIL, InspectionResult.NEEDS_FOLLOW_UP]:
        if not final_condition_notes or not final_condition_notes.strip():
            raise ValidationError("Condition notes/reason required for fail or needs_follow_up result")

    inspection.result = final_result
    inspection.observations = final_observations
    if checklist is not None:
        inspection.checklist = checklist
    inspection.condition_notes = final_condition_notes
    inspection.is_finalized = True
    inspection.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(inspection)

    from app.services.application import transition_application_status
    transition_application_status(db, application, ApplicationStatus.INSPECTION_RECORDED, inspector, "Inspection finalized")

    create_audit_event(
        db, inspector.id, "finalize_inspection", "inspection", inspection.id,
        new_status=final_result.value, reason=final_observations
    )
    return inspection


def update_inspection(
    db: Session,
    inspection_id: int,
    inspector: User,
    **kwargs,
) -> Inspection:
    inspection = get_inspection(db, inspection_id, inspector)

    if inspection.is_finalized and inspector.role not in [UserRole.REGULATOR, UserRole.ADMIN]:
        raise ValidationError("Finalized inspections cannot be modified")

    if "result" in kwargs and kwargs["result"] is not None:
        if inspection.is_finalized and inspector.role not in [UserRole.REGULATOR, UserRole.ADMIN]:
            raise ValidationError("Cannot change result of finalized inspection")

    for key, value in kwargs.items():
        if value is not None and hasattr(inspection, key):
            setattr(inspection, key, value)

    db.commit()
    db.refresh(inspection)
    create_audit_event(
        db, inspector.id, "update_inspection", "inspection", inspection.id,
        reason="Inspection updated"
    )
    return inspection