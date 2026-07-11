import uuid
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.access_log import AccessLog

def build_feature_vector(user_id: uuid.UUID, event_time: datetime, db: Session) -> pd.DataFrame:
    """
    Computes trailing 24-hour CERT feature approximations over PostgreSQL access logs.

    Approximations & Mappings to CERT features:
    - CERT total_logins: Count of 'login' type events in trailing 24h.
    - CERT unique_login_pcs: Number of distinct devices used for 'login' events in trailing 24h.
      Maps to unique device IDs observed in login events.
    - CERT avg_login_hour: The mean hour of day of all login events. Defaults to 12.0 if no logins.
    - CERT off_hour_logins: Count of login events occurring outside core hours (before 6 AM or at/after 8 PM).
    - CERT total_device_events: Total count of events associated with a physical device (non-null device_id).
      Maps to device-tagged events (approximate of USB/device connection events).
    - CERT unique_devices: Number of distinct physical devices observed in trailing 24h.
    - CERT off_hour_device: Count of device-tagged events occurring in off-hours.
    - CERT files_accessed: Total file interactions, represented by 'file_download' and 'repo_access' events.
    - CERT unique_files: Distinct files or resources interacted with across file access events.
    - CERT unique_content: Distinct resources targeted by 'file_download' events only.
    - CERT off_hour_file: Count of file interaction events in off-hours.
    - CERT files_per_login: Ratio of files accessed to total logins. Defaults to files_accessed if total_logins = 0.
    - CERT device_login_ratio: Ratio of device events to total logins. Defaults to total_device_events if total_logins = 0.
    - CERT off_hour_ratio: Ratio of all off-hour events to all events in the 24h window.
    """
    start_time = event_time - timedelta(days=1)

    # Retrieve all access logs for the specified user in the trailing 24-hour window
    logs = db.query(AccessLog).filter(
        AccessLog.user_id == user_id,
        AccessLog.event_time >= start_time,
        AccessLog.event_time <= event_time
    ).all()

    # Filtered lists for feature aggregation
    login_logs = [l for l in logs if l.event_type == "login"]
    file_logs = [l for l in logs if l.event_type in ("file_download", "repo_access")]
    download_logs = [l for l in logs if l.event_type == "file_download"]
    device_logs = [l for l in logs if l.device_id is not None]

    # Helper function to check if a log occurred during off-hours (before 6:00 AM or after/at 8:00 PM)
    def is_off_hour(log: AccessLog) -> bool:
        return log.event_time.hour >= 20 or log.event_time.hour < 6

    # 1. total_logins
    total_logins = len(login_logs)

    # 2. unique_login_pcs
    unique_login_pcs = len({l.device_id for l in login_logs if l.device_id is not None})

    # 3. avg_login_hour
    if login_logs:
        avg_login_hour = sum(l.event_time.hour for l in login_logs) / total_logins
    else:
        avg_login_hour = 12.0

    # 4. off_hour_logins
    off_hour_logins = sum(1 for l in login_logs if is_off_hour(l))

    # 5. total_device_events
    total_device_events = len(device_logs)

    # 6. unique_devices
    unique_devices = len({l.device_id for l in logs if l.device_id is not None})

    # 7. off_hour_device
    off_hour_device = sum(1 for l in device_logs if is_off_hour(l))

    # 8. files_accessed
    files_accessed = len(file_logs)

    # 9. unique_files
    unique_files = len({l.resource for l in file_logs if l.resource is not None})

    # 10. unique_content
    unique_content = len({l.resource for l in download_logs if l.resource is not None})

    # 11. off_hour_file
    off_hour_file = sum(1 for l in file_logs if is_off_hour(l))

    # 12. files_per_login
    files_per_login = files_accessed / max(total_logins, 1)

    # 13. device_login_ratio
    device_login_ratio = total_device_events / max(total_logins, 1)

    # 14. off_hour_ratio
    total_events = len(logs)
    off_hour_events = sum(1 for l in logs if is_off_hour(l))
    off_hour_ratio = off_hour_events / max(total_events, 1)

    # Construct single-row DataFrame with the exact column order expected by the models
    feature_dict = {
        "total_logins": float(total_logins),
        "unique_login_pcs": float(unique_login_pcs),
        "avg_login_hour": float(avg_login_hour),
        "off_hour_logins": float(off_hour_logins),
        "total_device_events": float(total_device_events),
        "unique_devices": float(unique_devices),
        "off_hour_device": float(off_hour_device),
        "files_accessed": float(files_accessed),
        "unique_files": float(unique_files),
        "unique_content": float(unique_content),
        "off_hour_file": float(off_hour_file),
        "files_per_login": float(files_per_login),
        "device_login_ratio": float(device_login_ratio),
        "off_hour_ratio": float(off_hour_ratio)
    }

    return pd.DataFrame([feature_dict])
