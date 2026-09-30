import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class NotificationType(str, enum.Enum):
    APPLICATION_SUBMITTED = "application_submitted"
    APPLICATION_UNDER_REVIEW = "application_under_review"
    CORRECTION_REQUESTED = "correction_requested"
    APPLICATION_REJECTED = "application_rejected"
    APPLICATION_APPROVED_SCHEDULING = "application_approved_scheduling"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    INSPECTION_RECORDED = "inspection_recorded"
    CERTIFICATE_ISSUED = "certificate_issued"
    CERTIFICATE_REVOKED = "certificate_revoked"
    CERTIFICATE_SUPERSEDED = "certificate_superseded"
    CERTIFICATE_EXPIRING_SOON = "certificate_expiring_soon"
    CERTIFICATE_EXPIRED = "certificate_expired"
    GENERAL = "general"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    reference_type = Column(String(100), nullable=True)
    reference_id = Column(Integer, nullable=True, index=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    delivery_status = Column(String(50), default="pending")

    recipient = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("ix_notification_recipient_unread", "recipient_id", "is_read"),
    )


from app.models.user import User

User.notifications = relationship("Notification", back_populates="recipient", lazy="dynamic")