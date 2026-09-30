import hashlib
import json
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent
from app.models.user import User
from app.core.permissions import has_permission, Permission


def _compute_event_hash(event: AuditEvent, previous_hash: Optional[str]) -> str:
    """Compute SHA-256 hash for an audit event, chained to previous event."""
    data = {
        "id": event.id,
        "actor_id": event.actor_id,
        "action": event.action,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "previous_status": event.previous_status,
        "new_status": event.new_status,
        "reason": event.reason,
        "request_metadata": event.request_metadata,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None,
        "previous_hash": previous_hash,
    }
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode()).hexdigest()


def create_audit_event(
    db: Session,
    actor_id: int,
    action: str,
    entity_type: str,
    entity_id: int,
    previous_status: Optional[str] = None,
    new_status: Optional[str] = None,
    reason: Optional[str] = None,
    request_metadata: Optional[str] = None,
) -> AuditEvent:
    # Get the previous event's hash for chaining
    previous_event = db.query(AuditEvent).order_by(AuditEvent.id.desc()).first()
    previous_hash = previous_event.event_hash if previous_event else None

    audit = AuditEvent(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_status=previous_status,
        new_status=new_status,
        reason=reason,
        request_metadata=request_metadata,
        timestamp=datetime.utcnow(),
        previous_hash=previous_hash,
    )
    db.add(audit)
    db.flush()  # Get the ID without committing

    # Compute and store the hash
    audit.event_hash = _compute_event_hash(audit, previous_hash)
    db.commit()
    db.refresh(audit)
    return audit


def verify_audit_chain(db: Session) -> Tuple[bool, List[dict]]:
    """Verify the integrity of the audit log hash chain.
    Returns (is_valid, list_of_errors)."""
    events = db.query(AuditEvent).order_by(AuditEvent.id).all()
    errors = []
    previous_hash = None

    for event in events:
        computed_hash = _compute_event_hash(event, previous_hash)
        if computed_hash != event.event_hash:
            errors.append({
                "event_id": event.id,
                "expected_hash": event.event_hash,
                "computed_hash": computed_hash,
            })
        previous_hash = event.event_hash

    return len(errors) == 0, errors


def list_audit_events(
    db: Session,
    user: User,
    page: int = 1,
    page_size: int = 50,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    actor_id: Optional[int] = None,
) -> Tuple[List[AuditEvent], int]:
    if not has_permission(user, Permission.AUDIT_READ):
        raise PermissionError("Not authorized to view audit events")

    query = db.query(AuditEvent)

    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
    if actor_id:
        query = query.filter(AuditEvent.actor_id == actor_id)

    total = query.count()
    events = query.order_by(AuditEvent.timestamp.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return events, total