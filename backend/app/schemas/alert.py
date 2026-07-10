import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class AlertResponse(BaseModel):
    id: uuid.UUID
    severity: str
    status: str
    created_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    trust_score: Optional[float] = None
    username: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

class AlertUpdate(BaseModel):
    status: str = Field(..., max_length=20)  # open, reviewed, escalated, dismissed
    reviewed_by: str = Field(..., max_length=100)
