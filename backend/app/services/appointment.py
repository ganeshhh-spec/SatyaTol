from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.core.errors import NotFoundError, ForbiddenError, ValidationError, ConflictError
from app.core.permissions import has_permission, Permission, can_access_application


def check_appointment_conflict(
    db: Session,
    assignee_id: int,
    start: datetime,
    end: datetime,
    exclude_id: Optional[int] = None,
) -> bool:
    query = db.query(Appointment).filter(
        and_(
            Appointment.assigned_officer_id == assignee_id,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.IN_PROGRESS]),
            Appointment.scheduled_start < end,
            Appointment.scheduled_end > start,
        )
    )
    if exclude_id:
        query = query.filter(Appointment.id != exclude_id)
    return query.first() is not None


def create_appointment(
    db: Session,
    application_id: int,
    assigned_officer_id: Optional[int],
    assigned_centre_id: Optional[int],
    scheduled_start: datetime,
    scheduled_end: datetime,
    location: Optional[str],
    mode: Optional[str],
) -> Appointment:
    appointment = Appointment(
        application_id=application_id,
        assigned_officer_id=assigned_officer_id,
        assigned_centre_id=assigned_centre_id,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        location=location,
        mode=mode,
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def get_appointment(db: Session, appointment_id: int, user: User) -> Appointment:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise NotFoundError("Appointment", appointment_id)

    application = appointment.application
    if not can_access_application(user, application.applicant_id, application.assigned_officer_id, application.jurisdiction):
        raise ForbiddenError()
    return appointment


def list_appointments(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status: Optional[AppointmentStatus] = None,
) -> Tuple[List[Appointment], int]:
    query = db.query(Appointment).join(Appointment.application)

    if user.role == UserRole.OWNER:
        query = query.filter(Appointment.application.has(applicant_id=user.id))
    elif user.role == UserRole.LMO:
        query = query.filter(Appointment.assigned_officer_id == user.id)
        if user.jurisdiction:
            query = query.filter(Application.jurisdiction == user.jurisdiction)
    elif user.role == UserRole.GATC:
        query = query.filter(Appointment.assigned_centre_id == user.id)

    if status:
        query = query.filter(Appointment.status == status)

    total = query.count()
    appointments = query.order_by(Appointment.scheduled_start.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return appointments, total


def update_appointment(
    db: Session,
    appointment_id: int,
    user: User,
    **kwargs,
) -> Appointment:
    if not has_permission(user, Permission.APPLICATION_SCHEDULE):
        raise ForbiddenError("Not authorized to update appointments")

    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise NotFoundError("Appointment", appointment_id)

    if "scheduled_start" in kwargs and "scheduled_end" in kwargs:
        new_start = kwargs["scheduled_start"]
        new_end = kwargs["scheduled_end"]
        if appointment.assigned_officer_id and check_appointment_conflict(
            db, appointment.assigned_officer_id, new_start, new_end, exclude_id=appointment_id
        ):
            raise ConflictError("Officer has a conflicting appointment")
        if appointment.assigned_centre_id and check_appointment_conflict(
            db, appointment.assigned_centre_id, new_start, new_end, exclude_id=appointment_id
        ):
            raise ConflictError("Centre has a conflicting appointment")

    for key, value in kwargs.items():
        if value is not None and hasattr(appointment, key):
            setattr(appointment, key, value)

    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(db: Session, appointment_id: int, user: User) -> Appointment:
    appointment = get_appointment(db, appointment_id, user)
    if not has_permission(user, Permission.APPLICATION_SCHEDULE):
        raise ForbiddenError("Not authorized to cancel appointments")

    appointment.status = AppointmentStatus.CANCELLED
    db.commit()
    db.refresh(appointment)
    return appointment