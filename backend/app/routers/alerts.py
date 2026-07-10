import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.alert import Alert
from app.models.trust_score import TrustScore
from app.models.user import User
from app.schemas.alert import AlertResponse, AlertUpdate
from app.auth.rbac import require_roles

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"]
)

@router.get("", response_model=List[AlertResponse], dependencies=[Depends(require_roles("admin", "analyst"))])
def get_alerts(
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve all security alerts. Includes filtering options by status and severity.
    Joins user and trust score tables for complete UI display.
    """
    query = db.query(
        Alert, 
        TrustScore.trust_score, 
        User.username,
        TrustScore.model_score_id
    ).outerjoin(
        TrustScore, Alert.trust_score_id == TrustScore.id
    ).outerjoin(
        User, TrustScore.user_id == User.id
    )

    if status_filter:
        query = query.filter(Alert.status == status_filter)
    if severity_filter:
        query = query.filter(Alert.severity == severity_filter)

    results = query.order_by(Alert.created_at.desc()).all()

    alerts_list = []
    for alert, trust_score, username, model_score_id in results:
        alerts_list.append(
            AlertResponse(
                id=alert.id,
                severity=alert.severity,
                status=alert.status,
                created_at=alert.created_at,
                reviewed_by=alert.reviewed_by,
                reviewed_at=alert.reviewed_at,
                trust_score=trust_score,
                username=username,
                trust_score_id=alert.trust_score_id,
                model_score_id=model_score_id
            )
        )
    return alerts_list

@router.patch("/{id}", response_model=AlertResponse, dependencies=[Depends(require_roles("admin", "analyst"))])
def update_alert(
    id: uuid.UUID,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db)
):
    """
    Update the status and reviewer of a specific security alert. 
    Triggers reviewed_at timestamp generation upon alert status changes.
    """
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )

    # Validate status transitions
    allowed_statuses = {"open", "reviewed", "escalated", "dismissed"}
    if alert_update.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid alert status. Must be one of {allowed_statuses}"
        )

    alert.status = alert_update.status
    alert.reviewed_by = alert_update.reviewed_by
    
    if alert_update.status in ("reviewed", "escalated", "dismissed"):
        alert.reviewed_at = datetime.utcnow()
    else:
        alert.reviewed_at = None

    db.commit()
    db.refresh(alert)

    # Retrieve context details for Response schema
    trust_score_val = None
    username_val = None
    if alert.trust_score:
        trust_score_val = alert.trust_score.trust_score
        if alert.trust_score.user:
            username_val = alert.trust_score.user.username

    return AlertResponse(
        id=alert.id,
        severity=alert.severity,
        status=alert.status,
        created_at=alert.created_at,
        reviewed_by=alert.reviewed_by,
        reviewed_at=alert.reviewed_at,
        trust_score=trust_score_val,
        username=username_val,
        trust_score_id=alert.trust_score_id,
        model_score_id=alert.trust_score.model_score_id if alert.trust_score else None
    )
