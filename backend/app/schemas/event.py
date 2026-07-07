import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class EventCreate(BaseModel):
    user_id: uuid.UUID
    device_fingerprint: str = Field(..., max_length=255)
    event_type: str = Field(..., max_length=50)  # login, repo_access, file_download, privilege_change, code_export
    resource: Optional[str] = Field(None, max_length=255)
    bytes_transferred: int = Field(0, ge=0)
    ip_address: Optional[str] = Field(None, max_length=45)
    location: Optional[str] = Field(None, max_length=100)

class EventResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    device_id: Optional[uuid.UUID]
    event_type: str
    resource: Optional[str]
    bytes_transferred: int
    event_time: datetime
    ip_address: Optional[str]
    location: Optional[str]

    model_config = {
        "from_attributes": True
    }
