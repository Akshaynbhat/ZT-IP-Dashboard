from fastapi import APIRouter, Depends, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.device import Device
from app.models.access_log import AccessLog
from app.schemas.event import EventCreate
from app.core.limiter import limiter
from app.worker.scheduled_scoring import run_scoring_cycle

router = APIRouter(
    prefix="/events",
    tags=["events"]
)

@router.post("", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("5/second")
def ingest_event(
    request: Request,
    event_data: EventCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):


    """
    Ingest a new developer activity event log. 
    Accepts logs from any authenticated user to support replay simulator and ingestion agents.
    """
    # Ensure target user exists in database (auto-provision placeholder if needed)
    user = db.query(User).filter(User.id == event_data.user_id, User.tenant_id == current_user.tenant_id).first()
    if not user:
        user = User(
            id=event_data.user_id,
            keycloak_sub=str(event_data.user_id),
            username=f"user_{str(event_data.user_id)[:8]}",
            email=f"user_{str(event_data.user_id)[:8]}@zt-enterprise.io",
            role="employee",
            department="Unknown",
            tenant_id=current_user.tenant_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Look up or create Device record for this specific user
    device = db.query(Device).filter(
        Device.device_fingerprint == event_data.device_fingerprint,
        Device.user_id == event_data.user_id,
        Device.tenant_id == current_user.tenant_id
    ).first()
    
    if not device:
        device = Device(
            user_id=event_data.user_id,
            device_fingerprint=event_data.device_fingerprint,
            os=event_data.os if hasattr(event_data, 'os') else "Unknown",
            is_known=False,
            tenant_id=current_user.tenant_id
        )
        db.add(device)
        db.commit()
        db.refresh(device)

    # Insert AccessLog record
    access_log = AccessLog(
        user_id=event_data.user_id,
        device_id=device.id,
        event_type=event_data.event_type,
        resource=event_data.resource,
        bytes_transferred=event_data.bytes_transferred,
        ip_address=event_data.ip_address,
        location=event_data.location,
        tenant_id=current_user.tenant_id
    )
    db.add(access_log)

    db.commit()
    db.refresh(access_log)

    background_tasks.add_task(run_scoring_cycle)

    return {
        "message": "event accepted",
        "log_id": str(access_log.id)
    }

