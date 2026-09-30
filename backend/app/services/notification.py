from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.core.config import settings


def create_notification(
    db: Session,
    recipient_id: int,
    type: NotificationType,
    title: str,
    message: str,
    reference_type: Optional[str] = None,
    reference_id: Optional[int] = None,
) -> Notification:
    notification = Notification(
        recipient_id=recipient_id,
        type=type,
        title=title,
        message=message,
        reference_type=reference_type,
        reference_id=reference_id,
        delivery_status="delivered",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notification(db: Session, notification_id: int, user: User) -> Notification:
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        from app.core.errors import NotFoundError
        raise NotFoundError("Notification", notification_id)
    if notification.recipient_id != user.id:
        from app.core.errors import ForbiddenError
        raise ForbiddenError()
    return notification


def list_notifications(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
) -> Tuple[List[Notification], int, int]:
    query = db.query(Notification).filter(Notification.recipient_id == user.id)

    if unread_only:
        query = query.filter(Notification.is_read == False)

    total = query.count()
    unread_count = db.query(Notification).filter(
        Notification.recipient_id == user.id, Notification.is_read == False
    ).count()

    notifications = query.order_by(Notification.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return notifications, total, unread_count


def mark_notification_read(db: Session, notification_id: int, user: User) -> Notification:
    notification = get_notification(db, notification_id, user)
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user: User) -> int:
    updated = db.query(Notification).filter(
        Notification.recipient_id == user.id, Notification.is_read == False
    ).update({"is_read": True, "read_at": datetime.utcnow()})
    db.commit()
    return updated


def check_and_create_expiry_reminders(db: Session) -> int:
    from app.models.certificate import Certificate, CertificateStatus
    from app.services.certificate import calculate_certificate_status

    certificates = db.query(Certificate).filter(
        Certificate.status.in_([CertificateStatus.VALID, CertificateStatus.EXPIRED])
    ).all()

    created = 0
    now = datetime.utcnow()

    for cert in certificates:
        current_status = calculate_certificate_status(cert)

        for window_days in settings.reminder_windows_list:
            reminder_date = cert.valid_until - timedelta(days=window_days)
            if reminder_date.date() <= now.date() < cert.valid_until.date():
                existing = db.query(Notification).filter(
                    Notification.recipient_id == cert.application.applicant_id,
                    Notification.type == NotificationType.CERTIFICATE_EXPIRING_SOON,
                    Notification.reference_type == "certificate",
                    Notification.reference_id == cert.id,
                ).first()
                if not existing:
                    create_notification(
                        db,
                        cert.application.applicant_id,
                        NotificationType.CERTIFICATE_EXPIRING_SOON,
                        f"Certificate expiring in {window_days} days",
                        f"Certificate {cert.certificate_number} for instrument {cert.instrument.serial_number} expires on {cert.valid_until.strftime('%Y-%m-%d')}.",
                        reference_type="certificate",
                        reference_id=cert.id,
                    )
                    created += 1

        if current_status == CertificateStatus.EXPIRED and cert.status == CertificateStatus.VALID:
            cert.status = CertificateStatus.EXPIRED
            existing = db.query(Notification).filter(
                Notification.recipient_id == cert.application.applicant_id,
                Notification.type == NotificationType.CERTIFICATE_EXPIRED,
                Notification.reference_type == "certificate",
                Notification.reference_id == cert.id,
            ).first()
            if not existing:
                create_notification(
                    db,
                    cert.application.applicant_id,
                    NotificationType.CERTIFICATE_EXPIRED,
                    "Certificate expired",
                    f"Certificate {cert.certificate_number} for instrument {cert.instrument.serial_number} has expired.",
                    reference_type="certificate",
                    reference_id=cert.id,
                )
                created += 1

    db.commit()
    return created