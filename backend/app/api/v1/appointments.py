from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentListResponse,
)
from app.services.appointment import (
    get_appointment,
    list_appointments,
    update_appointment,
    cancel_appointment,
)
from app.models.user import User
from app.models.appointment import AppointmentStatus
from app.core.errors import NotFoundError, ForbiddenError, ValidationError, ConflictError

router = APIRouter(tags=["appointments"])


@router.get("", response_model=AppointmentListResponse)
def list_appointments_endpoint(
    page: int = 1,
    page_size: int = 20,
    status: Optional[AppointmentStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    appointments, total = list_appointments(db, current_user, page, page_size, status)
    return {"items": appointments, "total": total, "page": page, "page_size": page_size}


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment_endpoint(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        appointment = get_appointment(db, appointment_id, current_user)
        return appointment
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment_endpoint(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        update_data = {k: v for k, v in appointment_data.model_dump().items() if v is not None}
        appointment = update_appointment(db, appointment_id, current_user, **update_data)
        return appointment
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment_endpoint(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        appointment = cancel_appointment(db, appointment_id, current_user)
        return appointment
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))