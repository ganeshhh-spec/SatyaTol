import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Index, Boolean, Date
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.instrument import InstrumentCategory
from app.models.user import User


class StandardType(str, enum.Enum):
    REFERENCE_WEIGHT = "reference_weight"
    VOLUME_MEASURE = "volume_measure"
    LENGTH_MEASURE = "length_measure"
    FLOW_MEASURE = "flow_measure"
    TEMPERATURE_STANDARD = "temperature_standard"
    OTHER = "other"


class StandardStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    UNDER_CALIBRATION = "under_calibration"
    RETIRED = "retired"
    LOST = "lost"


class Standard(Base):
    __tablename__ = "standards"

    id = Column(Integer, primary_key=True, index=True)
    standard_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    standard_type = Column(SQLEnum(StandardType), nullable=False, index=True)
    nominal_value = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=False)
    accuracy_class = Column(String(50), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    serial_number = Column(String(100), nullable=True)
    
    # Calibration tracking
    calibration_date = Column(Date, nullable=True, index=True)
    calibration_due_date = Column(Date, nullable=True, index=True)
    calibration_certificate_number = Column(String(100), nullable=True)
    calibration_lab = Column(String(255), nullable=True)
    calibration_status = Column(SQLEnum(StandardStatus), default=StandardStatus.ACTIVE, nullable=False)
    
    # Ownership and location
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    location = Column(Text, nullable=True)
    custodian_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Status and metadata
    status = Column(SQLEnum(StandardStatus), default=StandardStatus.ACTIVE, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_standards")
    custodian = relationship("User", foreign_keys=[custodian_id], back_populates="custodied_standards")
    usages = relationship("StandardUsage", back_populates="standard", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_standard_calibration_due", "calibration_due_date", "calibration_status"),
        Index("ix_standard_owner_status", "owner_id", "status"),
    )


class StandardUsage(Base):
    __tablename__ = "standard_usages"

    id = Column(Integer, primary_key=True, index=True)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False, index=True)
    inspection_id = Column(Integer, ForeignKey("inspections.id", ondelete="SET NULL"), nullable=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True, index=True)
    used_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    purpose = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    standard = relationship("Standard", back_populates="usages")
    user = relationship("User")

    __table_args__ = (
        Index("ix_standard_usage_standard_date", "standard_id", "used_at"),
    )


class EnforcementCaseType(str, enum.Enum):
    CONSUMER_COMPLAINT = "consumer_complaint"
    SHORT_WEIGHT_MEASURE = "short_weight_measure"
    UNVERIFIED_INSTRUMENT = "unverified_instrument"
    TAMPERED_INSTRUMENT = "tampered_instrument"
    EXPIRED_CERTIFICATE = "expired_certificate"
    NON_COMPLIANT_LABEL = "non_compliant_label"
    OTHER = "other"


class EnforcementCaseStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_INVESTIGATION = "under_investigation"
    EVIDENCE_COLLECTION = "evidence_collection"
    HEARING_SCHEDULED = "hearing_scheduled"
    DECIDED = "decided"
    APPEALED = "appealed"
    CLOSED = "closed"
    DISMISSED = "dismissed"


class EnforcementCase(Base):
    __tablename__ = "enforcement_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    case_type = Column(SQLEnum(EnforcementCaseType), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Parties involved
    complainant_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    respondent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=True, index=True)
    
    # Jurisdiction and assignment
    jurisdiction = Column(String(255), nullable=True, index=True)
    assigned_officer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Status and dates
    status = Column(SQLEnum(EnforcementCaseStatus), default=EnforcementCaseStatus.OPEN, nullable=False, index=True)
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
    target_resolution_date = Column(DateTime, nullable=True)
    
    # Outcome
    outcome = Column(Text, nullable=True)
    penalty_amount = Column(Integer, nullable=True)
    penalty_paid = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    complainant = relationship("User", foreign_keys=[complainant_id], back_populates="filed_cases")
    respondent = relationship("User", foreign_keys=[respondent_id], back_populates="responded_cases")
    instrument = relationship("Instrument", back_populates="enforcement_cases")
    assigned_officer = relationship("User", foreign_keys=[assigned_officer_id], back_populates="assigned_enforcement_cases")
    evidence = relationship("EnforcementEvidence", back_populates="case", cascade="all, delete-orphan")
    actions = relationship("EnforcementAction", back_populates="case", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_enforcement_case_status_date", "status", "opened_at"),
        Index("ix_enforcement_case_officer_status", "assigned_officer_id", "status"),
    )


class EnforcementEvidence(Base):
    __tablename__ = "enforcement_evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("enforcement_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type = Column(String(50), nullable=False)  # document, photo, measurement, witness
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_hash = Column(String(64), nullable=True)  # SHA-256
    collected_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_sealed = Column(Boolean, default=False)
    seal_number = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("EnforcementCase", back_populates="evidence")
    collector = relationship("User")

    __table_args__ = (
        Index("ix_enforcement_evidence_case", "case_id", "collected_at"),
    )


class EnforcementAction(Base):
    __tablename__ = "enforcement_actions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("enforcement_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)  # notice, seizure, hearing, fine, closure
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    performed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, overdue
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("EnforcementCase", back_populates="actions")
    performer = relationship("User")

    __table_args__ = (
        Index("ix_enforcement_action_case_status", "case_id", "status"),
    )


class RepairRecord(Base):
    __tablename__ = "repair_records"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    
    # Repair details
    repair_type = Column(String(50), nullable=False)  # routine, breakdown, seal_replacement, adjustment
    description = Column(Text, nullable=False)
    performed_by = Column(String(255), nullable=True)  # repairer name/firm
    repairer_license = Column(String(100), nullable=True)
    
    # Dates
    repair_date = Column(Date, nullable=False, index=True)
    next_due_date = Column(Date, nullable=True)
    
    # Seal management
    old_seal_number = Column(String(100), nullable=True)
    new_seal_number = Column(String(100), nullable=True)
    seal_broken_reason = Column(Text, nullable=True)
    
    # Verification
    requires_reverification = Column(Boolean, default=True)
    re_verification_application_id = Column(Integer, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    
    # Cost and approval
    cost = Column(Integer, nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Documentation
    work_order_number = Column(String(100), nullable=True)
    invoice_number = Column(String(100), nullable=True)
    attachment_path = Column(String(500), nullable=True)
    attachment_hash = Column(String(64), nullable=True)
    
    # Status
    status = Column(String(50), default="completed")  # completed, pending_approval, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instrument = relationship("Instrument", back_populates="repair_records")
    application = relationship("Application", foreign_keys=[application_id])
    re_verification_application = relationship("Application", foreign_keys=[re_verification_application_id])
    approver = relationship("User", foreign_keys=[approved_by_id])

    __table_args__ = (
        Index("ix_repair_instrument_date", "instrument_id", "repair_date"),
        Index("ix_repair_seal", "old_seal_number", "new_seal_number"),
    )


from app.models.user import User
from app.models.instrument import Instrument
from app.models.application import Application
from app.models.inspection import Inspection

User.owned_standards = relationship("Standard", foreign_keys=[Standard.owner_id], back_populates="owner", lazy="dynamic")
User.custodied_standards = relationship("Standard", foreign_keys=[Standard.custodian_id], back_populates="custodian", lazy="dynamic")
User.filed_cases = relationship("EnforcementCase", foreign_keys=[EnforcementCase.complainant_id], back_populates="complainant", lazy="dynamic")
User.responded_cases = relationship("EnforcementCase", foreign_keys=[EnforcementCase.respondent_id], back_populates="respondent", lazy="dynamic")
User.assigned_enforcement_cases = relationship("EnforcementCase", foreign_keys=[EnforcementCase.assigned_officer_id], back_populates="assigned_officer", lazy="dynamic")

Instrument.enforcement_cases = relationship("EnforcementCase", back_populates="instrument", lazy="dynamic")
Instrument.repair_records = relationship("RepairRecord", back_populates="instrument", lazy="dynamic")