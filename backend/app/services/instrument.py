from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.instrument import Instrument, InstrumentCategory, InstrumentStatus
from app.models.application import Application, ApplicationStatus
from app.models.appointment import Appointment
from app.models.inspection import Inspection
from app.models.certificate import Certificate, CertificateStatus
from app.models.audit import AuditEvent
from app.models.user import User, UserRole
from app.core.errors import NotFoundError, ForbiddenError, ValidationError, ConflictError
from app.core.permissions import can_access_instrument


def create_instrument(
    db: Session,
    owner: User,
    category: InstrumentCategory,
    instrument_type: str,
    manufacturer: str,
    model: str,
    serial_number: str,
    capacity: Optional[str] = None,
    unit: Optional[str] = None,
    location: Optional[str] = None,
    use_context: Optional[str] = None,
) -> Instrument:
    existing = (
        db.query(Instrument)
        .filter(Instrument.owner_id == owner.id, Instrument.serial_number == serial_number)
        .first()
    )
    if existing:
        raise ConflictError("Instrument with this serial number already exists for this owner")

    instrument = Instrument(
        owner_id=owner.id,
        category=category,
        instrument_type=instrument_type,
        manufacturer=manufacturer,
        model=model,
        serial_number=serial_number,
        capacity=capacity,
        unit=unit,
        location=location,
        use_context=use_context,
    )
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument


def get_instrument(db: Session, instrument_id: int, user: User) -> Instrument:
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)
    if not can_access_instrument(user, instrument.owner_id):
        raise ForbiddenError()
    return instrument


def get_instrument_history(db: Session, instrument_id: int, user: User) -> dict:
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise NotFoundError("Instrument", instrument_id)
    if not can_access_instrument(user, instrument.owner_id):
        raise ForbiddenError()

    applications = db.query(Application).filter(Application.instrument_id == instrument_id).order_by(Application.created_at).all()
    appointments = db.query(Appointment).join(Application).filter(Application.instrument_id == instrument_id).order_by(Appointment.scheduled_start).all()
    inspections = db.query(Inspection).join(Application).filter(Application.instrument_id == instrument_id).order_by(Inspection.inspection_date).all()
    certificates = db.query(Certificate).filter(Certificate.instrument_id == instrument_id).order_by(Certificate.issue_date).all()
    audit_events = db.query(AuditEvent).filter(
        (AuditEvent.entity_type == "instrument") & (AuditEvent.entity_id == instrument_id)
    ).order_by(AuditEvent.timestamp).all()

    application_events = []
    for app in applications:
        app_audits = db.query(AuditEvent).filter(
            (AuditEvent.entity_type == "application") & (AuditEvent.entity_id == app.id)
        ).order_by(AuditEvent.timestamp).all()
        application_events.append({
            "application": app,
            "audits": app_audits,
        })

    timeline = []

    timeline.append({
        "date": instrument.created_at,
        "type": "instrument_registered",
        "title": "Instrument Registered",
        "details": f"{instrument.manufacturer} {instrument.model} (Serial: {instrument.serial_number}) registered",
        "entity_type": "instrument",
        "entity_id": instrument.id,
    })

    for app in applications:
        timeline.append({
            "date": app.submitted_at or app.created_at,
            "type": "application_submitted",
            "title": f"Application Submitted ({app.verification_type.value})",
            "details": f"Application #{app.id} - {app.status.value.replace('_', ' ').title()}",
            "entity_type": "application",
            "entity_id": app.id,
        })
        for audit in application_events:
            if audit["application"].id == app.id:
                for ae in audit["audits"]:
                    timeline.append({
                        "date": ae.timestamp,
                        "type": "application_" + ae.action,
                        "title": f"Application {ae.action.replace('_', ' ').title()}",
                        "details": ae.reason or f"Status changed: {ae.previous_status} → {ae.new_status}",
                        "entity_type": "application",
                        "entity_id": app.id,
                    })

    for appt in appointments:
        timeline.append({
            "date": appt.scheduled_start,
            "type": "appointment_scheduled",
            "title": "Appointment Scheduled",
            "details": f"Appointment #{appt.id} at {appt.location or 'TBD'}",
            "entity_type": "appointment",
            "entity_id": appt.id,
        })

    for insp in inspections:
        timeline.append({
            "date": insp.inspection_date,
            "type": "inspection_recorded",
            "title": f"Inspection {insp.result.value.upper()}" + (" (Draft)" if not insp.is_finalized else " (Finalized)"),
            "details": f"By {insp.inspector.full_name if insp.inspector else 'Unknown'} - {insp.observations[:100] if insp.observations else 'No observations'}",
            "entity_type": "inspection",
            "entity_id": insp.id,
        })

    for cert in certificates:
        timeline.append({
            "date": cert.issue_date,
            "type": "certificate_issued",
            "title": f"Certificate Issued: {cert.certificate_number}",
            "details": f"Valid from {cert.valid_from.strftime('%Y-%m-%d')} to {cert.valid_until.strftime('%Y-%m-%d')}",
            "entity_type": "certificate",
            "entity_id": cert.id,
        })
        if cert.status == CertificateStatus.REVOKED:
            timeline.append({
                "date": cert.revoked_at,
                "type": "certificate_revoked",
                "title": f"Certificate Revoked: {cert.certificate_number}",
                "details": cert.revocation_reason or "No reason provided",
                "entity_type": "certificate",
                "entity_id": cert.id,
            })
        elif cert.status == CertificateStatus.SUPERSEDED:
            timeline.append({
                "date": cert.updated_at,
                "type": "certificate_superseded",
                "title": f"Certificate Superseded: {cert.certificate_number}",
                "details": f"Superseded by certificate #{cert.superseded_by_id}",
                "entity_type": "certificate",
                "entity_id": cert.id,
            })

    timeline.sort(key=lambda x: x["date"] or datetime.min)

    return {
        "instrument": instrument,
        "applications": applications,
        "appointments": appointments,
        "inspections": inspections,
        "certificates": certificates,
        "audit_events": audit_events,
        "timeline": timeline,
    }


def list_instruments(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    category: Optional[InstrumentCategory] = None,
    status: Optional[InstrumentStatus] = None,
    search: Optional[str] = None,
) -> tuple[List[Instrument], int]:
    query = db.query(Instrument)

    if user.role == UserRole.OWNER:
        query = query.filter(Instrument.owner_id == user.id)

    if category:
        query = query.filter(Instrument.category == category)
    if status:
        query = query.filter(Instrument.status == status)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Instrument.serial_number.ilike(search_term),
                Instrument.manufacturer.ilike(search_term),
                Instrument.model.ilike(search_term),
            )
        )

    total = query.count()
    instruments = query.order_by(Instrument.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return instruments, total


def update_instrument(
    db: Session,
    instrument_id: int,
    user: User,
    **kwargs,
) -> Instrument:
    instrument = get_instrument(db, instrument_id, user)
    if user.role == UserRole.OWNER and instrument.owner_id != user.id:
        raise ForbiddenError()

    for key, value in kwargs.items():
        if value is not None and hasattr(instrument, key):
            setattr(instrument, key, value)

    db.commit()
    db.refresh(instrument)
    return instrument


def delete_instrument(db: Session, instrument_id: int, user: User) -> None:
    instrument = get_instrument(db, instrument_id, user)
    if user.role == UserRole.OWNER and instrument.owner_id != user.id:
        raise ForbiddenError()

    db.delete(instrument)
    db.commit()