from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.db.session import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=False, index=True)
    previous_status = Column(String(100), nullable=True)
    new_status = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    request_metadata = Column(Text, nullable=True)
    # Hash chaining for integrity
    event_hash = Column(String(64), nullable=True)
    previous_hash = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    actor = relationship("User", back_populates="audit_events")

    __table_args__ = (
        Index("ix_audit_entity", "entity_type", "entity_id"),
        Index("ix_audit_actor_time", "actor_id", "timestamp"),
    )


from app.models.user import User
User.audit_events = relationship("AuditEvent", back_populates="actor", lazy="dynamic")