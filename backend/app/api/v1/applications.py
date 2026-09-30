from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationSubmit,
    ApplicationReview,
    ApplicationSchedule,
    ApplicationResponse,
    ApplicationListResponse,
    ApplicationDetailResponse,
)
from app.schemas.attachment import AttachmentResponse
from app.services.application import (
    create_application,
    submit_application,
    get_application,
    list_applications,
    review_application,
    resubmit_application,
    schedule_application,
)
from app.services.attachment import create_attachment, get_attachment
from app.models.user import User
from app.models.application import ApplicationStatus, VerificationType
from app.core.errors import NotFoundError, ForbiddenError, ValidationError, ConflictError
import os
import uuid
from app.core.config import settings

router = APIRouter(tags=["applications"])


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application_endpoint(
    application_data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        application = create_application(db, current_user, **application_data.model_dump())
        return application
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{application_id}/submit", response_model=ApplicationResponse)
def submit_application_endpoint(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        application = submit_application(db, application_id, current_user)
        return application
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.get("", response_model=ApplicationListResponse)
def list_applications_endpoint(
    page: int = 1,
    page_size: int = 20,
    status: Optional[ApplicationStatus] = None,
    verification_type: Optional[VerificationType] = None,
    instrument_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    applications, total = list_applications(db, current_user, page, page_size, status, verification_type, instrument_id)
    return {"items": applications, "total": total, "page": page, "page_size": page_size}


@router.get("/{application_id}", response_model=ApplicationDetailResponse)
def get_application_endpoint(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        application = get_application(db, application_id, current_user)
        return application
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.post("/{application_id}/review", response_model=ApplicationResponse)
def review_application_endpoint(
    application_id: int,
    review_data: ApplicationReview,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        application = review_application(db, application_id, current_user, review_data.action, review_data.reason or "")
        return application
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{application_id}/resubmit", response_model=ApplicationResponse)
def resubmit_application_endpoint(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        application = resubmit_application(db, application_id, current_user)
        return application
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/{application_id}/schedule", response_model=ApplicationResponse)
def schedule_application_endpoint(
    application_id: int,
    schedule_data: ApplicationSchedule,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        application = schedule_application(
            db,
            application_id,
            current_user,
            schedule_data.assigned_officer_id,
            schedule_data.assigned_centre_id,
            schedule_data.scheduled_start,
            schedule_data.scheduled_end,
            schedule_data.location,
            schedule_data.mode,
        )
        return application
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{application_id}/attachments", response_model=AttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    application_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.services.application import get_application
    from app.services.attachment import create_attachment
    from app.models.attachment import Attachment

    try:
        application = get_application(db, application_id, current_user)
        if application.applicant_id != current_user.id:
            raise ForbiddenError("Only applicant can upload attachments")

        if file.content_type not in settings.allowed_attachment_types_list:
            raise ValidationError(f"File type not allowed. Allowed: {settings.allowed_attachment_types_list}")

        file_content = await file.read()
        if len(file_content) > settings.max_upload_size_mb * 1024 * 1024:
            raise ValidationError(f"File size exceeds {settings.max_upload_size_mb}MB limit")

        os.makedirs(settings.upload_dir, exist_ok=True)
        ext = os.path.splitext(file.filename)[1] if file.filename else ""
        storage_key = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(settings.upload_dir, storage_key)

        with open(file_path, "wb") as f:
            f.write(file_content)

        attachment = create_attachment(
            db,
            application_id=application_id,
            filename=file.filename or "unknown",
            media_type=file.content_type,
            storage_key=storage_key,
            uploader_id=current_user.id,
        )
        return attachment
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))