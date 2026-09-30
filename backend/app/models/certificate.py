import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base


class CertificateStatus(str, enum.Enum):
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUPERSEDED = "superseded"


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False, index=True)
    certificate_number = Column(String(100), unique=True, nullable=False, index=True)
    verification_token = Column(String(64), unique=True, nullable=False, index=True)
    issue_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_until = Column(DateTime, nullable=False)
    status = Column(SQLEnum(CertificateStatus), default=CertificateStatus.VALID, nullable=False, index=True)
    issuer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    revocation_reason = Column(Text, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    superseded_by_id = Column(Integer, ForeignKey("certificates.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    application = relationship("Application", back_populates="certificates")
    instrument = relationship("Instrument", back_populates="certificates")
    issuer = relationship("User", back_populates="issued_certificates")
    superseded_by = relationship("Certificate", remote_side=[id], back_populates="supersedes")
    supersedes = relationship("Certificate", back_populates="superseded_by")

    __table_args__ = (
        Index("ix_certificate_instrument_status", "instrument_id", "status"),
        Index("ix_certificate_valid_until", "valid_until"),
    )


from app.models.application import Application
from app.models.instrument import Instrument
from app.models.user import User

Application.certificates = relationship("Certificate", back_populates="application", lazy="dynamic")
Instrument.certificates = relationship("Certificate", back_populates="instrument", lazy="dynamic")
User.issued_certificates = relationship("Certificate", back_populates="issuer", lazy="dynamic")