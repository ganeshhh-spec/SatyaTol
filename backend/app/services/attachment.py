from typing import Optional
from sqlalchemy.orm import Session
from app.models.attachment import Attachment
from app.core.errors import NotFoundError, ForbiddenError


def create_attachment(
    db: Session,
    application_id: int,
    filename: str,
    media_type: str,
    storage_key: str,
    uploader_id: int,
) -> Attachment:
    attachment = Attachment(
        application_id=application_id,
        filename=filename,
        media_type=media_type,
        storage_key=storage_key,
        uploader_id=uploader_id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def get_attachment(db: Session, attachment_id: int, user_id: int) -> Attachment:
    attachment = db.query(Attachment).filter(Attachment.id == attachment_id).first()
    if not attachment:
        raise NotFoundError("Attachment", attachment_id)
    return attachment