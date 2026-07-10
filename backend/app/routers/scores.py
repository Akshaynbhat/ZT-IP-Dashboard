import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.trust_score import TrustScore
from app.models.model_score import ModelScore
from app.schemas.score import TrustScoreResponse, ExplanationResponse, SHAPFeature
from app.auth.rbac import require_roles

router = APIRouter(
    prefix="/scores",
    tags=["scores"]
)

@router.get("", response_model=List[TrustScoreResponse], dependencies=[Depends(require_roles("admin", "analyst"))])
def get_riskiest_scores(
    db: Session = Depends(get_db)
):
    """
    Retrieve the latest trust score for each user, sorted ascending (lowest trust/riskiest first).
    Accessible by admins and analysts.
    """
    # Subquery to identify the latest trust score calculation per user
    latest_score_subquery = db.query(
        TrustScore.user_id,
        func.max(TrustScore.computed_at).label("latest_at")
    ).group_by(TrustScore.user_id).subquery()

    # Query latest scores and sort them ascending
    scores = db.query(TrustScore).join(
        latest_score_subquery,
        (TrustScore.user_id == latest_score_subquery.c.user_id) &
        (TrustScore.computed_at == latest_score_subquery.c.latest_at)
    ).order_by(TrustScore.trust_score.asc()).all()

    return scores

@router.get("/{id}/explanation", response_model=ExplanationResponse, dependencies=[Depends(require_roles("admin", "analyst"))])
def get_score_explanation(
    id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve the SHAP explanation associated with a specific model score event.
    Returns the top 3 features contributing to the risk classification.
    """
    # Look up model score entry
    model_score = db.query(ModelScore).filter(ModelScore.id == id).first()
    if not model_score:
        # Check if the id matches access_log_id to be extra helpful
        model_score = db.query(ModelScore).filter(ModelScore.access_log_id == id).first()
        if not model_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Model score evaluation record not found"
            )

    # Process and sort SHAP values
    raw_shap = model_score.shap_values or []
    
    # Sort features by absolute contribution to show strongest indicators
    sorted_shap = sorted(
        raw_shap,
        key=lambda x: abs(x.get("shap_value") or x.get("value") or 0.0),
        reverse=True
    )

    shap_top_features = []
    for item in sorted_shap:
        val = item.get("shap_value") or item.get("value") or 0.0
        # Positive values increase the risk probability (pushing decision to malicious)
        direction = "increase" if val >= 0 else "decrease"
        
        shap_top_features.append(
            SHAPFeature(
                feature=item.get("feature", "Unknown Feature"),
                shap_value=val,
                direction=direction
            )
        )

    # Limit to top 3 feature reasons
    top_3_features = shap_top_features[:3]

    return ExplanationResponse(
        shap_top_features=top_3_features,
        risk_class=model_score.risk_class,
        risk_probability=model_score.risk_probability,
        anomaly_score=model_score.anomaly_score
    )
