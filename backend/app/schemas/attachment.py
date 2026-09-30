from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AttachmentBase(BaseModel):
    filename: str
    media_type: str


class AttachmentCreate(AttachmentBase):
    application_id: int
    storage_key: str


class AttachmentResponse(AttachmentBase):
    id: int
    application_id: int
    uploader_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True