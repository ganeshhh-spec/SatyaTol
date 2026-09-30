import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class InstrumentCategory(str, enum.Enum):
    WEIGHING_NON_AUTOMATIC = "weighing_non_automatic"
    WEIGHING_AUTOMATIC = "weighing_automatic"
    MEASURING_LENGTH = "measuring_length"
    MEASURING_VOLUME = "measuring_volume"
    MEASURING_FLOW = "measuring_flow"
    OTHER = "other"


class InstrumentStatus(str, enum.Enum):
    REGISTERED = "registered"
    UNDER_VERIFICATION = "under_verification"
    VERIFIED = "verified"
    EXPIRED = "expired"
    REJECTED = "rejected"


class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(SQLEnum(InstrumentCategory), nullable=False)
    instrument_type = Column(String(100), nullable=False)
    manufacturer = Column(String(255), nullable=False)
    model = Column(String(100), nullable=False)
    serial_number = Column(String(100), nullable=False, index=True)
    capacity = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    location = Column(Text, nullable=True)
    use_context = Column(Text, nullable=True)
    registration_date = Column(DateTime, default=datetime.utcnow)
    status = Column(SQLEnum(InstrumentStatus), default=InstrumentStatus.REGISTERED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="instruments")

    __table_args__ = (
        Index("ix_instrument_owner_serial", "owner_id", "serial_number", unique=True),
    )


from app.models.user import User
User.instruments = relationship("Instrument", back_populates="owner", lazy="dynamic")