from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.instrument import Instrument, InstrumentCategory, InstrumentStatus
from app.models.application import Application, ApplicationStatus, VerificationType
from app.models.certificate import Certificate, CertificateStatus
from app.models.user import User, UserRole
from app.core.permissions import has_permission, Permission


def search_instruments(
    db: Session,
    user: User,
    query: Optional[str] = None,
    category: Optional[InstrumentCategory] = None,
    status: Optional[InstrumentStatus] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Instrument], int]:
    base_query = db.query(Instrument)

    if user.role == UserRole.OWNER:
        base_query = base_query.filter(Instrument.owner_id == user.id)
    elif not has_permission(user, Permission.INSTRUMENT_READ_ALL):
        raise PermissionError("Not authorized")

    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Instrument.serial_number.ilike(search_term),
                Instrument.manufacturer.ilike(search_term),
                Instrument.model.ilike(search_term),
            )
        )
    if category:
        base_query = base_query.filter(Instrument.category == category)
    if status:
        base_query = base_query.filter(Instrument.status == status)

    total = base_query.count()
    instruments = base_query.order_by(Instrument.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return instruments, total


def search_applications(
    db: Session,
    user: User,
    query: Optional[str] = None,
    status: Optional[ApplicationStatus] = None,
    verification_type: Optional[VerificationType] = None,
    instrument_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Application], int]:
    base_query = db.query(Application)

    if user.role == UserRole.OWNER:
        base_query = base_query.filter(Application.applicant_id == user.id)
    elif user.role == UserRole.LMO:
        base_query = base_query.filter(Application.assigned_officer_id == user.id)
    elif user.role == UserRole.GATC:
        base_query = base_query.filter(Application.assigned_centre_id == user.id)
    elif not has_permission(user, Permission.APPLICATION_READ_ALL):
        raise PermissionError("Not authorized")

    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Application.id.cast(String).ilike(search_term),
            )
        )
    if status:
        base_query = base_query.filter(Application.status == status)
    if verification_type:
        base_query = base_query.filter(Application.verification_type == verification_type)
    if instrument_id:
        base_query = base_query.filter(Application.instrument_id == instrument_id)

    total = base_query.count()
    applications = base_query.order_by(Application.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return applications, total


def search_certificates(
    db: Session,
    user: User,
    query: Optional[str] = None,
    status: Optional[CertificateStatus] = None,
    instrument_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Certificate], int]:
    base_query = db.query(Certificate).join(Application)

    if user.role == UserRole.OWNER:
        base_query = base_query.filter(Application.applicant_id == user.id)
    elif not has_permission(user, Permission.CERTIFICATE_READ_ALL):
        raise PermissionError("Not authorized")

    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Certificate.certificate_number.ilike(search_term),
                Certificate.verification_token.ilike(search_term),
            )
        )
    if status:
        base_query = base_query.filter(Certificate.status == status)
    if instrument_id:
        base_query = base_query.filter(Certificate.instrument_id == instrument_id)

    total = base_query.count()
    certificates = base_query.order_by(Certificate.issue_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return certificates, total


from sqlalchemy import String