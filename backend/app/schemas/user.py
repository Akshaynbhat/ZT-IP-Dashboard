import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.score import TrustScoreResponse
from app.schemas.event import EventResponse

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: str
    department: Optional[str] = None
    created_at: datetime
    current_trust_score: Optional[float] = None

    model_config = {
        "from_attributes": True
    }

class UserHistoryResponse(BaseModel):
    user: UserResponse
    trust_scores: List[TrustScoreResponse]
    recent_events: List[EventResponse]
