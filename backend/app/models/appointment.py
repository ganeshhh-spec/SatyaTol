import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    assigned_centre_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    scheduled_start = Column(DateTime, nullable=False, index=True)
    scheduled_end = Column(DateTime, nullable=False)
    location = Column(Text, nullable=True)
    mode = Column(String(50), nullable=True)
    status = Column(SQLEnum(AppointmentStatus), default=AppointmentStatus.SCHEDULED, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship("Application", back_populates="appointments")
    assigned_officer = relationship("User", foreign_keys=[assigned_officer_id], back_populates="officer_appointments")
    assigned_centre = relationship("User", foreign_keys=[assigned_centre_id], back_populates="centre_appointments")

    __table_args__ = (
        Index("ix_appointment_officer_time", "assigned_officer_id", "scheduled_start", "scheduled_end"),
        Index("ix_appointment_centre_time", "assigned_centre_id", "scheduled_start", "scheduled_end"),
    )


from app.models.application import Application
from app.models.user import User

Application.appointments = relationship("Appointment", back_populates="application", lazy="dynamic")
User.officer_appointments = relationship("Appointment", foreign_keys=[Appointment.assigned_officer_id], back_populates="assigned_officer", lazy="dynamic")
User.centre_appointments = relationship("Appointment", foreign_keys=[Appointment.assigned_centre_id], back_populates="assigned_centre", lazy="dynamic")