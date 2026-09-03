from sqlalchemy.orm import Session
from .models import PolicySettings, Case
import json

def check_policy(db: Session, case_amount: float, action: str) -> dict:
    """
    Check merchant policies for a given action and amount.
    Returns:
        {
            "approved": bool,
            "approval_required": bool,
            "escalate": bool,
            "reason": str
        }
    """
    policy = db.query(PolicySettings).filter(PolicySettings.id == "default").first()
    if not policy:
        # Default fallback rules if not in database
        return {
            "approved": case_amount < 10000.0,
            "approval_required": case_amount >= 10000.0,
            "escalate": False,
            "reason": "Default safety rules applied. Amounts >= ₹10,000 require approval."
        }

    # Load allowed actions
    try:
        allowed_actions = json.loads(policy.allowed_actions)
    except Exception:
        allowed_actions = []

    # 1. Action verification
    if action not in allowed_actions:
        return {
            "approved": False,
            "approval_required": True,
            "escalate": True,
            "reason": f"Action '{action}' is disabled by merchant policy."
        }

    # 2. Threshold checks
    if case_amount >= policy.require_approval_threshold:
        return {
            "approved": False,
            "approval_required": True,
            "escalate": False,
            "reason": f"Amount ₹{case_amount:,.2f} exceeds require-approval threshold of ₹{policy.require_approval_threshold:,.2f}."
        }
    
    if case_amount >= policy.auto_approve_threshold:
        return {
            "approved": False,
            "approval_required": True,
            "escalate": False,
            "reason": f"Amount ₹{case_amount:,.2f} falls between auto-approve (₹{policy.auto_approve_threshold:,.2f}) and require-approval thresholds."
        }

    # 3. Under threshold - Auto approve
    return {
        "approved": True,
        "approval_required": False,
        "escalate": False,
        "reason": f"Amount ₹{case_amount:,.2f} is within the auto-approve threshold of ₹{policy.auto_approve_threshold:,.2f}."
    }
