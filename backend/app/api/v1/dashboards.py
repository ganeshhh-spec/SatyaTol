from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import get_dashboard
from app.models.user import User

router = APIRouter(tags=["dashboards"])


@router.get("", response_model=DashboardResponse)
def get_dashboard_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_dashboard(db, current_user)