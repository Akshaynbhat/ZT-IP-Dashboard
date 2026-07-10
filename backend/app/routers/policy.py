import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.policy_rule import PolicyRule
from app.schemas.policy import PolicyRuleResponse, PolicyRuleUpdate
from app.auth.rbac import require_roles

router = APIRouter(
    prefix="/policy-rules",
    tags=["policy-rules"]
)

@router.get("", response_model=List[PolicyRuleResponse], dependencies=[Depends(require_roles("admin"))])
def get_policy_rules(
    db: Session = Depends(get_db)
):
    """
    Retrieve all security policy rules. Admin access only.
    """
    return db.query(PolicyRule).order_by(PolicyRule.threshold_min.asc()).all()

@router.put("/{id}", response_model=PolicyRuleResponse, dependencies=[Depends(require_roles("admin"))])
def update_policy_rule(
    id: uuid.UUID,
    rule_update: PolicyRuleUpdate,
    db: Session = Depends(get_db)
):
    """
    Update thresholds and action mapped to a policy rule. 
    Enforces check constraints to ensure active rule ranges do not overlap.
    """
    rule = db.query(PolicyRule).filter(PolicyRule.id == id).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy rule not found"
        )

    p_min = rule_update.threshold_min
    p_max = rule_update.threshold_max

    if p_min >= p_max:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="threshold_min must be strictly less than threshold_max"
        )

    # Verify overlap checks if the rule is activated
    if rule_update.active:
        other_active_rules = db.query(PolicyRule).filter(
            PolicyRule.active == True,
            PolicyRule.id != id
        ).all()

        for active_rule in other_active_rules:
            # Overlap check formula: max(start1, start2) < min(end1, end2)
            if max(p_min, active_rule.threshold_min) < min(p_max, active_rule.threshold_max):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Configuration overlap: Range [{p_min}, {p_max}] overlaps with "
                        f"active policy rule '{active_rule.rule_name}' [{active_rule.threshold_min}, {active_rule.threshold_max}]"
                    )
                )

    rule.threshold_min = p_min
    rule.threshold_max = p_max
    rule.action = rule_update.action
    rule.active = rule_update.active

    db.commit()
    db.refresh(rule)
    return rule
