from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.schemas.notification import NotificationListResponse
from app.services.notification import list_notifications, mark_notification_read, mark_all_read
from app.models.user import User

router = APIRouter(tags=["notifications"])


@router.get("", response_model=NotificationListResponse)
def list_notifications_endpoint(
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notifications, total, unread_count = list_notifications(db, current_user, page, page_size, unread_only)
    return {"items": notifications, "total": total, "page": page, "page_size": page_size, "unread_count": unread_count}


@router.post("/{notification_id}/read")
def mark_notification_read_endpoint(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.notification import mark_notification_read
    notification = mark_notification_read(db, notification_id, current_user)
    return {"success": True, "notification_id": notification.id}


@router.post("/read-all")
def mark_all_notifications_read_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.notification import mark_all_read
    count = mark_all_read(db, current_user)
    return {"success": True, "marked_read": count}