import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class InspectionResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_FOLLOW_UP = "needs_follow_up"


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    inspector_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    inspection_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    observations = Column(Text, nullable=True)
    checklist = Column(Text, nullable=True)
    condition_notes = Column(Text, nullable=True)
    result = Column(SQLEnum(InspectionResult), nullable=False)
    photos = Column(Text, nullable=True)
    signature_metadata = Column(Text, nullable=True)
    is_finalized = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship("Application", back_populates="inspections")
    inspector = relationship("User", back_populates="inspections")
    appointment = relationship("Appointment", back_populates="inspections")

    __table_args__ = (
        Index("ix_inspection_application_result", "application_id", "result"),
    )


from app.models.application import Application
from app.models.user import User
from app.models.appointment import Appointment

Application.inspections = relationship("Inspection", back_populates="application", lazy="dynamic")
User.inspections = relationship("Inspection", back_populates="inspector", lazy="dynamic")
Appointment.inspections = relationship("Inspection", back_populates="appointment", lazy="dynamic")