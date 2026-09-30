import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Text, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.instrument import InstrumentCategory


class RequirementSourceType(str, enum.Enum):
    LEGAL_METROLOGY_ACT = "legal_metrology_act"
    GENERAL_RULES = "general_rules"
    STATE_RULES = "state_rules"
    OFFICIAL_NOTIFICATION = "official_notification"
    OTHER = "other"


class VerificationRequirement(Base):
    __tablename__ = "verification_requirements"

    id = Column(Integer, primary_key=True, index=True)
    instrument_category = Column(SQLEnum(InstrumentCategory), nullable=False, index=True)
    requirement_code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(SQLEnum(RequirementSourceType), nullable=False)
    source_reference = Column(String(255), nullable=False)
    source_section = Column(String(100), nullable=True)
    effective_from = Column(DateTime, nullable=False, default=datetime.utcnow)
    effective_until = Column(DateTime, nullable=True)
    jurisdiction = Column(String(255), nullable=True)
    is_mandatory = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_requirement_category_effective", "instrument_category", "effective_from"),
        Index("ix_requirement_source", "source_type", "source_reference"),
    )


class ChecklistTemplate(Base):
    __tablename__ = "checklist_templates"

    id = Column(Integer, primary_key=True, index=True)
    instrument_category = Column(SQLEnum(InstrumentCategory), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False, default="1.0")
    source_requirement_ids = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime, nullable=False, default=datetime.utcnow)
    effective_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("ChecklistItem", back_populates="template", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_checklist_template_category_active", "instrument_category", "is_active"),
    )


class ChecklistItem(Base):
    __tablename__ = "checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("checklist_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    item_code = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    expected_result = Column(Text, nullable=True)
    is_mandatory = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    template = relationship("ChecklistTemplate", back_populates="items")


from app.models.requirement import VerificationRequirement, ChecklistTemplate, ChecklistItem