import uuid
from datetime import datetime, date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.certificate import Certificate, CertificateStatus
from app.models.application import Application, ApplicationStatus
from app.models.inspection import Inspection, InspectionResult
from app.models.instrument import Instrument
from app.models.user import User, UserRole
from app.core.errors import NotFoundError, ForbiddenError, ValidationError
from app.core.permissions import is_authorized_issuer, has_permission, Permission
from app.core.config import settings
from app.services.audit import create_audit_event


def calculate_certificate_status(certificate: Certificate) -> CertificateStatus:
    if certificate.status == CertificateStatus.REVOKED:
        return CertificateStatus.REVOKED
    if certificate.status == CertificateStatus.SUPERSEDED:
        return CertificateStatus.SUPERSEDED
    if datetime.utcnow() > certificate.valid_until:
        return CertificateStatus.EXPIRED
    return CertificateStatus.VALID


def issue_certificate(
    db: Session,
    issuer: User,
    application_id: int,
    valid_from: datetime,
    valid_until: datetime,
) -> Certificate:
    if not is_authorized_issuer(issuer):
        raise ForbiddenError("Only authorized LMOs can issue certificates")

    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise NotFoundError("Application", application_id)

    if application.status != ApplicationStatus.DECISION_PENDING:
        raise ValidationError("Application must be in decision_pending state")

    if application.status in [ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN, ApplicationStatus.CANCELLED]:
        raise ValidationError(f"Cannot issue certificate for application with status: {application.status.value}")

    # Check for failed or needs_followup inspections first
    failed_inspection = (
        db.query(Inspection)
        .filter(
            Inspection.application_id == application_id,
            Inspection.result.in_([InspectionResult.FAIL, InspectionResult.NEEDS_FOLLOW_UP]),
            Inspection.is_finalized == True
        )
        .first()
    )
    if failed_inspection:
        raise ValidationError(f"Cannot issue certificate: inspection result is {failed_inspection.result.value}")

    passing_inspection = (
        db.query(Inspection)
        .filter(
            Inspection.application_id == application_id,
            Inspection.result == InspectionResult.PASS,
            Inspection.is_finalized == True
        )
        .first()
    )
    if not passing_inspection:
        raise ValidationError("A finalized passing inspection is required to issue a certificate")

    existing_cert = (
        db.query(Certificate)
        .filter(Certificate.application_id == application_id)
        .first()
    )
    if existing_cert:
        raise ValidationError("A certificate already exists for this application. Use supersede if replacing.")

    certificate_number = f"LM-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    verification_token = uuid.uuid4().hex

    certificate = Certificate(
        application_id=application_id,
        instrument_id=application.instrument_id,
        certificate_number=certificate_number,
        verification_token=verification_token,
        issue_date=datetime.utcnow(),
        valid_from=valid_from,
        valid_until=valid_until,
        status=CertificateStatus.VALID,
        issuer_id=issuer.id,
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)

    from app.services.application import transition_application_status
    transition_application_status(db, application, ApplicationStatus.COMPLETED, issuer, "Certificate issued")

    create_audit_event(
        db, issuer.id, "issue_certificate", "certificate", certificate.id,
        new_status=CertificateStatus.VALID.value,
        reason=f"Certificate {certificate_number} issued for application {application_id}"
    )
    return certificate


def revoke_certificate(
    db: Session,
    actor: User,
    certificate_id: int,
    reason: str,
) -> Certificate:
    if not is_authorized_issuer(actor):
        raise ForbiddenError("Only authorized LMOs can revoke certificates")

    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not certificate:
        raise NotFoundError("Certificate", certificate_id)

    if certificate.status in [CertificateStatus.REVOKED, CertificateStatus.SUPERSEDED]:
        raise ValidationError("Certificate is already revoked or superseded")

    certificate.status = CertificateStatus.REVOKED
    certificate.revocation_reason = reason
    certificate.revoked_at = datetime.utcnow()
    db.commit()
    db.refresh(certificate)

    create_audit_event(
        db, actor.id, "revoke_certificate", "certificate", certificate.id,
        previous_status=CertificateStatus.VALID.value, new_status=CertificateStatus.REVOKED.value, reason=reason
    )
    return certificate


def supersede_certificate(
    db: Session,
    actor: User,
    certificate_id: int,
    reason: str,
    new_certificate_id: int,
) -> Certificate:
    if not is_authorized_issuer(actor):
        raise ForbiddenError("Only authorized LMOs can supersede certificates")

    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not certificate:
        raise NotFoundError("Certificate", certificate_id)

    new_certificate = db.query(Certificate).filter(Certificate.id == new_certificate_id).first()
    if not new_certificate:
        raise NotFoundError("New Certificate", new_certificate_id)

    if certificate.status in [CertificateStatus.REVOKED, CertificateStatus.SUPERSEDED]:
        raise ValidationError("Certificate is already revoked or superseded")

    certificate.status = CertificateStatus.SUPERSEDED
    certificate.superseded_by_id = new_certificate_id
    db.commit()
    db.refresh(certificate)

    create_audit_event(
        db, actor.id, "supersede_certificate", "certificate", certificate.id,
        previous_status=CertificateStatus.VALID.value, new_status=CertificateStatus.SUPERSEDED.value, reason=reason
    )
    return certificate


def get_certificate(db: Session, certificate_id: int, user: User) -> Certificate:
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not certificate:
        raise NotFoundError("Certificate", certificate_id)

    from app.core.permissions import can_access_application
    if not can_access_application(user, certificate.application.applicant_id, certificate.application.assigned_officer_id, certificate.application.jurisdiction):
        raise ForbiddenError()
    return certificate


def get_certificate_by_token(db: Session, token: str) -> Optional[Certificate]:
    return db.query(Certificate).filter(Certificate.verification_token == token).first()


def get_certificate_by_number(db: Session, number: str) -> Optional[Certificate]:
    return db.query(Certificate).filter(Certificate.certificate_number == number).first()


def list_certificates(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    status: Optional[CertificateStatus] = None,
    instrument_id: Optional[int] = None,
) -> Tuple[List[Certificate], int]:
    query = db.query(Certificate).join(Certificate.application)

    if user.role == UserRole.OWNER:
        query = query.filter(Application.applicant_id == user.id)
    elif user.role == UserRole.LMO:
        if user.jurisdiction:
            query = query.filter(Application.jurisdiction == user.jurisdiction)
    elif user.role == UserRole.GATC:
        query = query.filter(Application.assigned_centre_id == user.id)

    if status:
        query = query.filter(Certificate.status == status)
    if instrument_id:
        query = query.filter(Certificate.instrument_id == instrument_id)

    total = query.count()
    certificates = query.order_by(Certificate.issue_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return certificates, total


def get_public_certificate_data(db: Session, token: str) -> Optional[dict]:
    certificate = get_certificate_by_token(db, token)
    if not certificate:
        certificate = db.query(Certificate).filter(Certificate.certificate_number == token).first()
    if not certificate:
        return None

    current_status = calculate_certificate_status(certificate)
    instrument = certificate.instrument

    serial_display = instrument.serial_number
    if len(serial_display) > 4:
        serial_display = serial_display[:2] + "***" + serial_display[-2:]

    return {
        "certificate_id": str(certificate.id),
        "certificate_number": certificate.certificate_number,
        "instrument_category": instrument.category.value if instrument.category else "N/A",
        "manufacturer": instrument.manufacturer,
        "model": instrument.model,
        "serial_number_masked": serial_display,
        "issue_date": certificate.issue_date,
        "valid_from": certificate.valid_from,
        "valid_until": certificate.valid_until,
        "status": current_status.value,
        "issuing_authority": "Legal Metrology Department (Prototype)",
        "issuing_office": certificate.issuer.organization or "N/A",
        "verified_at": datetime.utcnow(),
        "is_prototype": True,
    }