from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.schemas.audit import AuditEventListResponse
from app.services.audit import list_audit_events
from app.models.user import User
from app.core.permissions import has_permission, Permission

router = APIRouter(tags=["audit"])


@router.get("", response_model=AuditEventListResponse)
def list_audit_events_endpoint(
    page: int = 1,
    page_size: int = 50,
    entity_type: str = None,
    entity_id: int = None,
    actor_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        events, total = list_audit_events(db, current_user, page, page_size, entity_type, entity_id, actor_id)
        return {"items": events, "total": total, "page": page, "page_size": page_size}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))