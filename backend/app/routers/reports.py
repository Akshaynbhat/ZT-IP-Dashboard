import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.access_log import AccessLog
from app.models.trust_score import TrustScore
from app.auth.rbac import require_roles

router = APIRouter(
    prefix="/reports",
    tags=["reports"]
)

@router.get("/access-logs/csv", dependencies=[Depends(require_roles("admin", "analyst"))])
def export_access_logs_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all access logs under the current tenant as a downloadable CSV.
    Accessible by administrators and security analysts.
    """
    logs = db.query(AccessLog, User.username).join(
        User, AccessLog.user_id == User.id
    ).filter(
        AccessLog.tenant_id == current_user.tenant_id
    ).order_by(AccessLog.event_time.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Event ID", "Timestamp (UTC)", "Username", "Event Type",
        "Target Resource", "Volume (Bytes)", "IP Address", "Geographic Location"
    ])

    for log, username in logs:
        writer.writerow([
            str(log.id),
            log.event_time.isoformat() if log.event_time else "",
            username,
            log.event_type,
            log.resource or "",
            log.bytes_transferred or 0,
            log.ip_address or "",
            log.location or ""
        ])

    output.seek(0)
    
    # Stream download response
    headers = {
        "Content-Disposition": "attachment; filename=access_logs_report.csv"
    }
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers=headers
    )

@router.get("/trust-scores/csv", dependencies=[Depends(require_roles("admin", "analyst"))])
def export_trust_scores_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export all trust score computation histories under the current tenant.
    """
    scores = db.query(TrustScore, User.username).join(
        User, TrustScore.user_id == User.id
    ).filter(
        TrustScore.tenant_id == current_user.tenant_id
    ).order_by(TrustScore.computed_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow([
        "Score ID", "Computed At (UTC)", "Username", "Trust Score",
        "Anomaly Factor", "Risk Factor"
    ])

    for score, username in scores:
        writer.writerow([
            str(score.id),
            score.computed_at.isoformat() if score.computed_at else "",
            username,
            round(score.trust_score, 2),
            round(score.anomaly_component, 2),
            round(score.risk_component, 2)
        ])

    output.seek(0)
    
    headers = {
        "Content-Disposition": "attachment; filename=trust_scores_report.csv"
    }
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers=headers
    )
