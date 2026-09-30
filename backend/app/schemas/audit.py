from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AuditEventResponse(BaseModel):
    id: int
    actor_id: int
    action: str
    entity_type: str
    entity_id: int
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    reason: Optional[str] = None
    request_metadata: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class AuditEventListResponse(BaseModel):
    items: list[AuditEventResponse]
    total: int
    page: int
    page_size: int