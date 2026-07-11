import logging
import uuid
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.access_log import AccessLog
from app.models.model_score import ModelScore
from app.models.trust_score import TrustScore
from app.models.device import Device
from app.models.policy_rule import PolicyRule
from app.models.alert import Alert
from app.ml import score_event
from app.ml.feature_adapter import build_feature_vector
from app.policy.policy_engine import evaluate_policy, get_alert_severity
from app.config import settings

logger = logging.getLogger(__name__)

# Initialize background scheduler instance
scheduler = AsyncIOScheduler()



def compute_identity_confidence(log: AccessLog, db: Session) -> float:
    """
    Calculates identity confidence score based on device and geolocation telemetry.
    """
    is_known = False
    if log.device_id:
        device = db.query(Device).filter(Device.id == log.device_id).first()
        if device:
            is_known = device.is_known

    # Verify if login location has been seen in the last 30 days
    location_match = False
    if log.location:
        thirty_days_ago = log.event_time - timedelta(days=30)
        seen_locations = db.query(AccessLog.location).filter(
            AccessLog.user_id == log.user_id,
            AccessLog.event_time >= thirty_days_ago,
            AccessLog.event_time < log.event_time,
            AccessLog.event_type == "login"
        ).distinct().all()
        
        seen_locs = {loc[0] for loc in seen_locations if loc[0]}
        location_match = log.location in seen_locs

    if is_known and location_match:
        return 1.0
    elif is_known or location_match:
        return 0.5
    else:
        return 0.0

async def run_scoring_cycle():
    """
    Executes the scheduled scoring cycle. Identifies and scores all unscored logs.
    """
    logger.info("Scanning for unscored events...")
    db = SessionLocal()
    try:
        # Find logs lacking a model score evaluation record
        unscored_logs = db.query(AccessLog).outerjoin(
            ModelScore, AccessLog.id == ModelScore.access_log_id
        ).filter(
            ModelScore.id == None
        ).order_by(AccessLog.event_time.asc()).all()

        if not unscored_logs:
            logger.info("No unscored access logs discovered.")
            return

        logger.info(f"Retrieved {len(unscored_logs)} unscored access logs to process.")

        for log in unscored_logs:
            try:
                # 1. Aggregate features using real ML feature adapter
                features = build_feature_vector(log.user_id, log.event_time, db)
                
                # 2. Call ML Engine stub
                ml_result = score_event(features)
                anomaly_score = ml_result["anomaly_score"]
                risk_class = ml_result["risk_class"]
                risk_probability = ml_result["risk_probability"]
                shap_values = ml_result["shap_values"]

                # 3. Determine identity confidence
                identity_confidence = compute_identity_confidence(log, db)

                # 4. Apply trust score formula
                trust_score = 100.0 * (
                    0.4 * (1.0 - anomaly_score) +
                    0.4 * (1.0 - risk_probability) +
                    0.2 * identity_confidence
                )
                trust_score = max(0.0, min(100.0, trust_score))

                # 5. Insert ModelScore
                model_score_record = ModelScore(
                    access_log_id=log.id,
                    anomaly_score=anomaly_score,
                    risk_class=risk_class,
                    risk_probability=risk_probability,
                    shap_values=shap_values,
                    scored_at=datetime.utcnow()
                )
                db.add(model_score_record)
                db.flush()

                # 6. Insert TrustScore
                trust_score_record = TrustScore(
                    user_id=log.user_id,
                    trust_score=trust_score,
                    anomaly_component=0.4 * (1.0 - anomaly_score),
                    risk_component=0.4 * (1.0 - risk_probability),
                    computed_at=datetime.utcnow(),
                    model_score_id=model_score_record.id
                )
                db.add(trust_score_record)
                db.flush()

                # 7. Evaluate security policy actions
                action = evaluate_policy(trust_score, db)
                logger.info(f"Scoring event {log.id} for user {log.user_id}. Trust score computed: {trust_score:.2f}. Policy Action: {action}")

                # 8. Create alerts on restriction/MFA triggers
                if action in ("restrict", "require_mfa"):
                    # Check for open alert duplicates in the last 15 minutes for this user
                    fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
                    existing_alert = db.query(Alert).join(TrustScore).filter(
                        TrustScore.user_id == log.user_id,
                        Alert.status == "open",
                        Alert.created_at >= fifteen_minutes_ago
                    ).first()

                    if not existing_alert:
                        severity = get_alert_severity(trust_score)
                        matching_rule = db.query(PolicyRule).filter(
                            PolicyRule.active == True,
                            PolicyRule.action == action,
                            PolicyRule.threshold_min <= trust_score,
                            PolicyRule.threshold_max > trust_score
                        ).first()

                        alert_record = Alert(
                            trust_score_id=trust_score_record.id,
                            policy_rule_id=matching_rule.id if matching_rule else None,
                            severity=severity,
                            status="open",
                            created_at=datetime.utcnow()
                        )
                        db.add(alert_record)
                        logger.warning(f"Alert created for user {log.user_id} due to score drop. Severity: {severity}")

                db.commit()

            except Exception as e:
                db.rollback()
                logger.error(f"Failed to score log transaction {log.id}: {str(e)}")

    except Exception as e:
        logger.error(f"Error during background worker execution: {str(e)}")
    finally:
        db.close()

def start_worker():
    """
    Configures and initiates the background scoring schedule.
    """
    scheduler.add_job(
        run_scoring_cycle,
        "interval",
        seconds=settings.SCORING_INTERVAL_SECONDS,
        id="scheduled_scoring_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Background worker started. Running every {settings.SCORING_INTERVAL_SECONDS} seconds.")

def shutdown_worker():
    """
    Shuts down the background scoring schedule.
    """
    scheduler.shutdown()
    logger.info("Background worker shut down.")
