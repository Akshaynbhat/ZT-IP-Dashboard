import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class TrustScoreResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    trust_score: float
    anomaly_component: float
    risk_component: float
    computed_at: datetime

    model_config = {
        "from_attributes": True
    }

class ModelScoreResponse(BaseModel):
    id: uuid.UUID
    access_log_id: Optional[uuid.UUID]
    anomaly_score: float
    risk_class: str
    risk_probability: float
    shap_values: list
    scored_at: datetime

    model_config = {
        "from_attributes": True
    }

class SHAPFeature(BaseModel):
    feature: str
    shap_value: float
    direction: str

class ExplanationResponse(BaseModel):
    shap_top_features: List[SHAPFeature]
    risk_class: str
    risk_probability: float
    anomaly_score: float
