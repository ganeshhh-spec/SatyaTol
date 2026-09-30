from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.schemas.instrument import (
    InstrumentCreate,
    InstrumentUpdate,
    InstrumentResponse,
    InstrumentListResponse,
    InstrumentHistoryResponse,
)
from app.services.instrument import (
    create_instrument,
    get_instrument,
    list_instruments,
    update_instrument,
    delete_instrument,
    get_instrument_history,
)
from app.models.user import User
from app.models.instrument import InstrumentCategory, InstrumentStatus
from app.core.errors import NotFoundError, ForbiddenError, ValidationError, ConflictError

router = APIRouter(tags=["instruments"])


@router.post("", response_model=InstrumentResponse, status_code=status.HTTP_201_CREATED)
def create_instrument_endpoint(
    instrument_data: InstrumentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        instrument = create_instrument(db, current_user, **instrument_data.model_dump())
        return instrument
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("", response_model=InstrumentListResponse)
def list_instruments_endpoint(
    page: int = 1,
    page_size: int = 20,
    category: Optional[InstrumentCategory] = None,
    status: Optional[InstrumentStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    instruments, total = list_instruments(db, current_user, page, page_size, category, status, search)
    return {"items": instruments, "total": total, "page": page, "page_size": page_size}


@router.get("/{instrument_id}", response_model=InstrumentResponse)
def get_instrument_endpoint(
    instrument_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        instrument = get_instrument(db, instrument_id, current_user)
        return instrument
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/{instrument_id}", response_model=InstrumentResponse)
def update_instrument_endpoint(
    instrument_id: int,
    instrument_data: InstrumentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        update_data = {k: v for k, v in instrument_data.model_dump().items() if v is not None}
        instrument = update_instrument(db, instrument_id, current_user, **update_data)
        return instrument
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{instrument_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instrument_endpoint(
    instrument_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        delete_instrument(db, instrument_id, current_user)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.get("/{instrument_id}/history", response_model=InstrumentHistoryResponse)
def get_instrument_history_endpoint(
    instrument_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        history = get_instrument_history(db, instrument_id, current_user)
        return history
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))