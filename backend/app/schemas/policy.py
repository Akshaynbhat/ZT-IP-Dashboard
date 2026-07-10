import uuid
from pydantic import BaseModel, Field

class PolicyRuleResponse(BaseModel):
    id: uuid.UUID
    rule_name: str
    threshold_min: float
    threshold_max: float
    action: str
    active: bool

    model_config = {
        "from_attributes": True
    }

class PolicyRuleUpdate(BaseModel):
    threshold_min: float = Field(..., ge=0.0, le=100.0)
    threshold_max: float = Field(..., ge=0.0, le=101.0)
    action: str = Field(..., max_length=50)  # allow, require_mfa, restrict
    active: bool
