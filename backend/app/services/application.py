from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.application import Application, VerificationType, ApplicationStatus
from app.models.instrument import Instrument
from app.models.user import User, UserRole
from app.models.attachment import Attachment
from app.core.errors import NotFoundError, ForbiddenError, ValidationError, ConflictError
from app.core.permissions import can_access_application, has_permission, Permission
from app.services.audit import create_audit_event


ALLOWED_TRANSITIONS = {
    ApplicationStatus.DRAFT: {ApplicationStatus.SUBMITTED},
    ApplicationStatus.SUBMITTED: {ApplicationStatus.UNDER_REVIEW},
    ApplicationStatus.UNDER_REVIEW: {
        ApplicationStatus.CORRECTION_REQUESTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.APPROVED_FOR_SCHEDULING,
    },
    ApplicationStatus.CORRECTION_REQUESTED: {ApplicationStatus.RESUBMITTED},
    ApplicationStatus.RESUBMITTED: {ApplicationStatus.UNDER_REVIEW},
    ApplicationStatus.APPROVED_FOR_SCHEDULING: {ApplicationStatus.SCHEDULED},
    ApplicationStatus.SCHEDULED: {ApplicationStatus.INSPECTION_IN_PROGRESS, ApplicationStatus.CANCELLED, ApplicationStatus.INSPECTION_RECORDED},
    ApplicationStatus.INSPECTION_IN_PROGRESS: {ApplicationStatus.INSPECTION_RECORDED},
    ApplicationStatus.INSPECTION_RECORDED: {ApplicationStatus.DECISION_PENDING},
    ApplicationStatus.DECISION_PENDING: {
        ApplicationStatus.COMPLETED,
        ApplicationStatus.CORRECTION_REQUESTED,
        ApplicationStatus.REJECTED,
    },
}


def can_transition(from_status: ApplicationStatus, to_status: ApplicationStatus) -> bool:
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())


def create_application(
    db: Session,
    applicant: User,
    instrument_id: int,
    verification_type: VerificationType,
    jurisdiction: Optional[str] = None,
    requested_appointment: Optional[datetime] = None,
    remarks: Optional[str] = None,
) -> Application:
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)

    if instrument.owner_id != applicant.id:
        raise ForbiddenError("You can only create applications for your own instruments")

    existing_active = (
        db.query(Application)
        .filter(
            Application.instrument_id == instrument_id,
            Application.status.in_([
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.UNDER_REVIEW,
                ApplicationStatus.CORRECTION_REQUESTED,
                ApplicationStatus.RESUBMITTED,
                ApplicationStatus.APPROVED_FOR_SCHEDULING,
                ApplicationStatus.SCHEDULED,
                ApplicationStatus.INSPECTION_IN_PROGRESS,
                ApplicationStatus.INSPECTION_RECORDED,
                ApplicationStatus.DECISION_PENDING,
            ]),
        )
        .first()
    )
    if existing_active:
        raise ConflictError("An active application already exists for this instrument")

    application = Application(
        instrument_id=instrument_id,
        applicant_id=applicant.id,
        verification_type=verification_type,
        jurisdiction=jurisdiction,
        requested_appointment=requested_appointment,
        remarks=remarks,
        status=ApplicationStatus.DRAFT,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def submit_application(db: Session, application_id: int, applicant: User) -> Application:
    application = get_application(db, application_id, applicant)
    if application.applicant_id != applicant.id:
        raise ForbiddenError("Only the applicant can submit the application")

    if application.status != ApplicationStatus.DRAFT:
        raise ValidationError("Only draft applications can be submitted")

    # Force load attachments
    attachment_count = db.query(Attachment).filter(Attachment.application_id == application_id).count()
    if attachment_count == 0:
        raise ValidationError("At least one attachment is required")

    transition_application_status(db, application, ApplicationStatus.SUBMITTED, applicant, "Application submitted")
    create_audit_event(
        db, applicant.id, "submit_application", "application", application.id,
        previous_status=ApplicationStatus.DRAFT.value, new_status=ApplicationStatus.SUBMITTED.value
    )
    return application


def get_application(db: Session, application_id: int, user: User) -> Application:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise NotFoundError("Application", application_id)
    if not can_access_application(user, application.applicant_id, application.assigned_officer_id, application.jurisdiction):
        raise ForbiddenError()
    return application


def list_applications(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status: Optional[ApplicationStatus] = None,
    verification_type: Optional[VerificationType] = None,
    instrument_id: Optional[int] = None,
) -> Tuple[List[Application], int]:
    query = db.query(Application)

    if user.role == UserRole.OWNER:
        query = query.filter(Application.applicant_id == user.id)
    elif user.role == UserRole.LMO:
        query = query.filter(Application.assigned_officer_id == user.id)
    elif user.role == UserRole.GATC:
        query = query.filter(Application.assigned_centre_id == user.id)

    if status:
        query = query.filter(Application.status == status)
    if verification_type:
        query = query.filter(Application.verification_type == verification_type)
    if instrument_id:
        query = query.filter(Application.instrument_id == instrument_id)

    total = query.count()
    applications = query.order_by(Application.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return applications, total


def transition_application_status(
    db: Session,
    application: Application,
    new_status: ApplicationStatus,
    actor: User,
    reason: Optional[str] = None,
) -> Application:
    if not can_transition(application.status, new_status):
        raise ValidationError(f"Invalid status transition from {application.status.value} to {new_status.value}")

    old_status = application.status
    application.status = new_status

    if new_status == ApplicationStatus.SUBMITTED:
        application.submitted_at = datetime.utcnow()
    elif new_status == ApplicationStatus.APPROVED_FOR_SCHEDULING:
        if not has_permission(actor, Permission.APPLICATION_REVIEW):
            raise ForbiddenError("Only authorized reviewers can approve for scheduling")

    db.commit()
    db.refresh(application)

    create_audit_event(
        db, actor.id, "status_transition", "application", application.id,
        previous_status=old_status.value, new_status=new_status.value, reason=reason
    )
    return application


def review_application(
    db: Session,
    application_id: int,
    reviewer: User,
    action: str,
    reason: str,
) -> Application:
    if not has_permission(reviewer, Permission.APPLICATION_REVIEW):
        raise ForbiddenError("Not authorized to review applications")

    application = get_application(db, application_id, reviewer)

    if application.status != ApplicationStatus.UNDER_REVIEW:
        raise ValidationError("Application is not under review")

    if action == "approve":
        transition_application_status(db, application, ApplicationStatus.APPROVED_FOR_SCHEDULING, reviewer, reason)
    elif action == "reject":
        if not reason:
            raise ValidationError("Rejection requires a reason")
        transition_application_status(db, application, ApplicationStatus.REJECTED, reviewer, reason)
    elif action == "request_correction":
        if not reason:
            raise ValidationError("Correction request requires a reason")
        transition_application_status(db, application, ApplicationStatus.CORRECTION_REQUESTED, reviewer, reason)
    else:
        raise ValidationError("Invalid review action")

    return application


def resubmit_application(db: Session, application_id: int, applicant: User) -> Application:
    application = get_application(db, application_id, applicant)
    if application.applicant_id != applicant.id:
        raise ForbiddenError("Only the applicant can resubmit")

    if application.status != ApplicationStatus.CORRECTION_REQUESTED:
        raise ValidationError("Application is not awaiting correction")

    transition_application_status(db, application, ApplicationStatus.RESUBMITTED, applicant, "Applicant resubmitted after correction")
    return application


def schedule_application(
    db: Session,
    application_id: int,
    scheduler: User,
    assigned_officer_id: Optional[int],
    assigned_centre_id: Optional[int],
    scheduled_start: datetime,
    scheduled_end: datetime,
    location: Optional[str],
    mode: Optional[str],
) -> Application:
    if not has_permission(scheduler, Permission.APPLICATION_SCHEDULE):
        raise ForbiddenError("Not authorized to schedule applications")

    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise NotFoundError("Application", application_id)

    if application.status != ApplicationStatus.APPROVED_FOR_SCHEDULING:
        raise ValidationError("Application must be approved for scheduling")

    if assigned_officer_id:
        officer = db.query(User).filter(User.id == assigned_officer_id).first()
        if not officer or officer.role != UserRole.LMO:
            raise ValidationError("Assigned officer must be an LMO")

    if assigned_centre_id:
        centre = db.query(User).filter(User.id == assigned_centre_id).first()
        if not centre or centre.role != UserRole.GATC:
            raise ValidationError("Assigned centre must be a GATC")

    from app.services.appointment import check_appointment_conflict
    if assigned_officer_id and check_appointment_conflict(db, assigned_officer_id, scheduled_start, scheduled_end):
        raise ConflictError("Officer has a conflicting appointment")
    if assigned_centre_id and check_appointment_conflict(db, assigned_centre_id, scheduled_start, scheduled_end):
        raise ConflictError("Centre has a conflicting appointment")

    application.assigned_officer_id = assigned_officer_id
    application.assigned_centre_id = assigned_centre_id
    transition_application_status(db, application, ApplicationStatus.SCHEDULED, scheduler, "Application scheduled")

    from app.services.appointment import create_appointment
    create_appointment(
        db,
        application_id=application_id,
        assigned_officer_id=assigned_officer_id,
        assigned_centre_id=assigned_centre_id,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        location=location,
        mode=mode,
    )

    return application