from sqlalchemy.orm import Session
from app.models.policy_rule import PolicyRule

def evaluate_policy(trust_score: float, db: Session) -> str:
    """
    Evaluates active policy rules from the database against a computed trust score.
    Returns the action for the first matching band. Defaults to 'allow'.
    """
    active_rules = db.query(PolicyRule).filter(
        PolicyRule.active == True
    ).order_by(PolicyRule.threshold_min.asc()).all()

    for rule in active_rules:
        # Check if score lies within rule boundaries: [threshold_min, threshold_max)
        # Using <= and < to handle upper limit exclusions cleanly
        if rule.threshold_min <= trust_score < rule.threshold_max:
            return rule.action

    return "allow"

def get_alert_severity(trust_score: float) -> str:
    """
    Determines alert severity levels depending on trust score bands.
    """
    if trust_score < 20.0:
        return "critical"
    elif 20.0 <= trust_score < 40.0:
        return "high"
    elif 40.0 <= trust_score < 70.0:
        return "medium"
    else:
        return "low"
