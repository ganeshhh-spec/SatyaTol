from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.schemas.inspection import (
    InspectionCreate,
    InspectionUpdate,
    InspectionFinalize,
    InspectionResponse,
    InspectionListResponse,
)
from app.services.inspection import (
    create_inspection,
    get_inspection,
    list_inspections,
    update_inspection,
    finalize_inspection,
)
from app.models.user import User
from app.models.inspection import InspectionResult
from app.core.errors import NotFoundError, ForbiddenError, ValidationError

router = APIRouter(tags=["inspections"])


@router.post("", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
def create_inspection_endpoint(
    inspection_data: InspectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        inspection = create_inspection(db, current_user, **inspection_data.model_dump())
        return inspection
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{inspection_id}/finalize", response_model=InspectionResponse)
def finalize_inspection_endpoint(
    inspection_id: int,
    finalize_data: InspectionFinalize,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        inspection = finalize_inspection(db, inspection_id, current_user, **finalize_data.model_dump(exclude_none=True))
        return inspection
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("", response_model=InspectionListResponse)
def list_inspections_endpoint(
    page: int = 1,
    page_size: int = 20,
    result: Optional[InspectionResult] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    inspections, total = list_inspections(db, current_user, page, page_size, result)
    return {"items": inspections, "total": total, "page": page, "page_size": page_size}


@router.get("/{inspection_id}", response_model=InspectionResponse)
def get_inspection_endpoint(
    inspection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        inspection = get_inspection(db, inspection_id, current_user)
        return inspection
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.patch("/{inspection_id}", response_model=InspectionResponse)
def update_inspection_endpoint(
    inspection_id: int,
    inspection_data: InspectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        update_data = {k: v for k, v in inspection_data.model_dump().items() if v is not None}
        inspection = update_inspection(db, inspection_id, current_user, **update_data)
        return inspection
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))