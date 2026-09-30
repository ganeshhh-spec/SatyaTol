import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class VerificationType(str, enum.Enum):
    INITIAL = "initial"
    REVERIFICATION = "reverification"


class ApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    CORRECTION_REQUESTED = "correction_requested"
    RESUBMITTED = "resubmitted"
    APPROVED_FOR_SCHEDULING = "approved_for_scheduling"
    SCHEDULED = "scheduled"
    INSPECTION_IN_PROGRESS = "inspection_in_progress"
    INSPECTION_RECORDED = "inspection_recorded"
    DECISION_PENDING = "decision_pending"
    COMPLETED = "completed"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    CANCELLED = "cancelled"


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False, index=True)
    applicant_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    verification_type = Column(SQLEnum(VerificationType), nullable=False)
    status = Column(SQLEnum(ApplicationStatus), default=ApplicationStatus.DRAFT, nullable=False, index=True)
    jurisdiction = Column(String(255), nullable=True)
    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    assigned_centre_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    requested_appointment = Column(DateTime, nullable=True)
    fee_amount = Column(Integer, nullable=True)
    fee_paid = Column(Boolean, default=False)
    remarks = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instrument = relationship("Instrument", back_populates="applications")
    applicant = relationship("User", foreign_keys=[applicant_id], back_populates="applications")
    assigned_officer = relationship("User", foreign_keys=[assigned_officer_id], back_populates="assigned_applications")
    assigned_centre = relationship("User", foreign_keys=[assigned_centre_id], back_populates="centre_applications")

    __table_args__ = (
        Index("ix_application_instrument_status", "instrument_id", "status"),
    )


from app.models.instrument import Instrument
from app.models.user import User

Instrument.applications = relationship("Application", back_populates="instrument", lazy="dynamic")
User.applications = relationship("Application", foreign_keys=[Application.applicant_id], back_populates="applicant", lazy="dynamic")
User.assigned_applications = relationship("Application", foreign_keys=[Application.assigned_officer_id], back_populates="assigned_officer", lazy="dynamic")
User.centre_applications = relationship("Application", foreign_keys=[Application.assigned_centre_id], back_populates="assigned_centre", lazy="dynamic")