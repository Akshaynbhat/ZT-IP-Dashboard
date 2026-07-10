import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.trust_score import TrustScore
from app.models.access_log import AccessLog
from app.schemas.user import UserResponse, UserHistoryResponse
from app.schemas.score import TrustScoreResponse
from app.schemas.event import EventResponse
from app.auth.rbac import require_roles

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("", response_model=List[UserResponse], dependencies=[Depends(require_roles("admin", "analyst"))])
def list_users(
    db: Session = Depends(get_db)
):
    """
    List all registered users alongside their current trust score.
    Accessible only by security administrators and analysts.
    """
    # Subquery to extract the latest computed_at for each user
    latest_score_subquery = db.query(
        TrustScore.user_id,
        func.max(TrustScore.computed_at).label("latest_at")
    ).group_by(TrustScore.user_id).subquery()

    # Outer join users with their latest trust score
    results = db.query(User, TrustScore).outerjoin(
        latest_score_subquery,
        User.id == latest_score_subquery.c.user_id
    ).outerjoin(
        TrustScore,
        (TrustScore.user_id == latest_score_subquery.c.user_id) &
        (TrustScore.computed_at == latest_score_subquery.c.latest_at)
    ).all()

    users_list = []
    for user, score in results:
        users_list.append(
            UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                role=user.role,
                department=user.department,
                created_at=user.created_at,
                current_trust_score=score.trust_score if score else None
            )
        )
    return users_list

@router.get("/{id}/history", response_model=UserHistoryResponse)
def get_user_history(
    id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve trust score time series and recent activity history for a user.
    Admins and analysts can view any user's history; employees are strictly restricted to their own.
    """
    # Enforce access control rules
    if current_user.role == "employee" and current_user.id != id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Employees are restricted from querying other users' security history"
        )

    # Verify user exists
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Fetch last 20 trust scores (ordered chronologically descending)
    scores = db.query(TrustScore).filter(
        TrustScore.user_id == id
    ).order_by(TrustScore.computed_at.desc()).limit(20).all()

    # Fetch last 20 access logs
    logs = db.query(AccessLog).filter(
        AccessLog.user_id == id
    ).order_by(AccessLog.event_time.desc()).limit(20).all()

    # Get current trust score (first in descending list, if any)
    latest_trust = scores[0].trust_score if scores else None

    user_response = UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        department=user.department,
        created_at=user.created_at,
        current_trust_score=latest_trust
    )

    # Convert to appropriate schemas
    return UserHistoryResponse(
        user=user_response,
        trust_scores=[TrustScoreResponse.model_validate(s) for s in scores],
        recent_events=[EventResponse.model_validate(l) for l in logs]
    )
