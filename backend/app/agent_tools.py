import datetime
import json
import random
import math
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from .models import (
    Customer, Invoice, PaymentAttempt, Promise, AdjustmentRefund,
    Case, RecoveryTransaction, InterventionFeedback, PolicySettings, AuditLog
)

# =========================================================================
# Event Logging Tool
# =========================================================================

def record_agent_event(db: Session, case_id: Optional[str], event_type: str, details: Dict[str, Any]):
    """
    Records a real backend agent event to the audit log stream.
    Supported event types:
    SCAN_STARTED, CASE_IDENTIFIED, TOOL_CALL_STARTED, TOOL_CALL_COMPLETED,
    EVIDENCE_RETRIEVED, CANDIDATE_ACTIONS_GENERATED, ACTION_EVALUATED,
    AGENT_DECISION, POLICY_CHECK, HUMAN_APPROVAL_REQUIRED, ACTION_EXECUTED,
    OUTCOME_RECEIVED, RECOVERY_RECORDED, LEARNING_UPDATED
    """
    entry = AuditLog(
        case_id=case_id,
        action=event_type,
        details=json.dumps(details),
        timestamp=datetime.datetime.utcnow()
    )
    db.add(entry)
    db.commit()

# =========================================================================
# Investigation Tools
# =========================================================================

def get_customer_profile(db: Session, customer_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the customer account details, segment, and account age.
    """
    cust = db.query(Customer).filter(Customer.id == customer_id).first()
    if not cust:
        return None
    return {
        "customer_id": cust.id,
        "name": cust.name,
        "email": cust.email,
        "segment": cust.segment,
        "payment_reliability": cust.payment_reliability,
        "account_created_at": cust.created_at.isoformat() if cust.created_at else None
    }

def get_payment_history(db: Session, customer_id: str) -> Dict[str, Any]:
    """
    Retrieves past completed and failed payment attempts for the customer across all invoices.
    """
    invoices = db.query(Invoice).filter(Invoice.customer_id == customer_id).all()
    invoice_ids = [inv.id for inv in invoices]
    
    attempts = db.query(PaymentAttempt).filter(PaymentAttempt.invoice_id.in_(invoice_ids)).all() if invoice_ids else []
    
    success_count = sum(1 for a in attempts if a.status == "SUCCESS")
    failed_count = sum(1 for a in attempts if a.status == "FAILED")
    total_paid = sum(a.amount for a in attempts if a.status == "SUCCESS")
    
    recent_errors = [a.error_code for a in attempts if a.status == "FAILED" and a.error_code][-5:]
    
    return {
        "total_invoices": len(invoices),
        "total_attempts": len(attempts),
        "successful_attempts": success_count,
        "failed_attempts": failed_count,
        "success_rate": round(success_count / len(attempts), 2) if attempts else 1.0,
        "total_paid_volume": round(total_paid, 2),
        "recent_error_codes": recent_errors
    }

# Backward compatibility alias
get_customer_payment_history = get_payment_history

def get_promise_history(db: Session, customer_id: str) -> Dict[str, Any]:
    """
    Calculates historical Promise-to-Pay compliance based on kept vs broken commitments.
    """
    promises = db.query(Promise).filter(Promise.customer_id == customer_id).all()
    
    kept = sum(1 for p in promises if p.status == "KEPT")
    broken = sum(1 for p in promises if p.status == "BROKEN")
    pending = sum(1 for p in promises if p.status == "PENDING")
    
    total_resolved = kept + broken
    reliability_score = round(kept / total_resolved, 2) if total_resolved > 0 else 0.50
    
    return {
        "total_promises": len(promises),
        "kept_promises": kept,
        "broken_promises": broken,
        "pending_promises": pending,
        "promise_reliability_score": reliability_score,
        "has_broken_history": broken > 0
    }

# Backward compatibility alias
get_customer_promise_history = get_promise_history

def get_invoice_details(db: Session, invoice_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves invoice amount, due date, status, and days overdue.
    """
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        return None
        
    anchor_time = datetime.datetime(2026, 8, 30, 12, 0, 0)
    days_overdue = max(0, (anchor_time - inv.due_date).days)
    
    paid = db.query(PaymentAttempt.amount).filter(
        PaymentAttempt.invoice_id == invoice_id,
        PaymentAttempt.status == "SUCCESS"
    ).scalar() or 0.0
    
    return {
        "invoice_id": inv.id,
        "customer_id": inv.customer_id,
        "total_amount": inv.amount,
        "paid_amount": round(paid, 2),
        "outstanding_balance": round(max(0.0, inv.amount - paid), 2),
        "status": inv.status,
        "due_date": inv.due_date.isoformat(),
        "days_overdue": days_overdue
    }

def get_payment_attempts(db: Session, invoice_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves all payment attempts for a specific invoice.
    """
    attempts = db.query(PaymentAttempt).filter(
        PaymentAttempt.invoice_id == invoice_id
    ).order_by(PaymentAttempt.created_at.desc()).all()
    
    return [
        {
            "attempt_id": a.id,
            "amount": a.amount,
            "status": a.status,
            "error_code": a.error_code,
            "timestamp": a.created_at.isoformat()
        }
        for a in attempts
    ]

def get_refund_history(db: Session, invoice_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves any refund records associated with this invoice.
    """
    refunds = db.query(AdjustmentRefund).filter(
        AdjustmentRefund.invoice_id == invoice_id,
        AdjustmentRefund.type == "REFUND"
    ).all()
    
    return [
        {
            "id": r.id,
            "type": "REFUND",
            "amount": r.amount,
            "reason": r.reason,
            "timestamp": r.created_at.isoformat()
        }
        for r in refunds
    ]

def get_adjustment_history(db: Session, invoice_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves discounts, co-marketing credits, or fee adjustments for an invoice.
    """
    adjustments = db.query(AdjustmentRefund).filter(
        AdjustmentRefund.invoice_id == invoice_id
    ).all()
    
    return [
        {
            "id": a.id,
            "type": a.type,
            "amount": a.amount,
            "reason": a.reason,
            "timestamp": a.created_at.isoformat()
        }
        for a in adjustments
    ]

def investigate_underpayment(db: Session, invoice_id: str) -> Dict[str, Any]:
    """
    Fintech Investigation Tool: Audits expected vs received amount and compares against adjustment credits & refunds.
    Returns:
    - RECOVERABLE: Unreconciled gap exists without legitimate discount.
    - NOT_RECOVERABLE: Gap is completely explained by legitimate credit or refund.
    - REQUIRES_HUMAN_INVESTIGATION: Conflicting offline notes.
    """
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        return {"reconciled": False, "status": "NOT_RECOVERABLE", "reason": "Invoice not found"}
        
    paid_amount = db.query(PaymentAttempt.amount).filter(
        PaymentAttempt.invoice_id == invoice_id,
        PaymentAttempt.status == "SUCCESS"
    ).scalar() or 0.0
    
    gap = round(inv.amount - paid_amount, 2)
    adjustments = db.query(AdjustmentRefund).filter(AdjustmentRefund.invoice_id == invoice_id).all()
    total_adjustments = sum(a.amount for a in adjustments)
    
    is_legitimate_discount = abs(gap - total_adjustments) <= 10.0 and total_adjustments > 0
    unreconciled_leak = max(0.0, round(gap - total_adjustments, 2))
    
    if is_legitimate_discount:
        result_status = "NOT_RECOVERABLE"
    elif unreconciled_leak > 0:
        result_status = "RECOVERABLE"
    else:
        result_status = "REQUIRES_HUMAN_INVESTIGATION"
    
    return {
        "invoice_amount": inv.amount,
        "paid_amount": paid_amount,
        "gap": gap,
        "total_adjustments": total_adjustments,
        "adjustment_reasons": [a.reason for a in adjustments],
        "is_legitimate_discount": is_legitimate_discount,
        "unreconciled_leak": unreconciled_leak,
        "investigation_status": result_status,
        "recommendation": "RESOLVE_LEGIT_DISCOUNT" if is_legitimate_discount else "RECOVER_UNRECONCILED_LEAK"
    }

def get_previous_interventions(db: Session, customer_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves previous agent recovery actions dispatched to this customer.
    """
    feedbacks = db.query(InterventionFeedback).filter(
        InterventionFeedback.customer_id == customer_id
    ).order_by(InterventionFeedback.created_at.desc()).limit(10).all()
    
    return [
        {
            "action": f.action,
            "issue_type": f.issue_type,
            "outcome": f.outcome,
            "success": f.success,
            "timestamp": f.created_at.isoformat()
        }
        for f in feedbacks
    ]

# =========================================================================
# Outcome Learning & Empirical Rates
# =========================================================================

def get_intervention_success_rates(db: Session, issue_type: str, action: str) -> Dict[str, Any]:
    """
    Bayesian-smoothed Historical Estimator:
    Combines domain prior with observed historical feedback records to compute empirical action effectiveness.
    """
    priors = {
        ("FAILED_PAYMENT", "retry_payment"): (8, 10),      # 80% prior
        ("FAILED_PAYMENT", "create_payment_link"): (6, 10),# 60% prior
        ("OVERDUE_PAYMENT", "send_payment_reminder"): (4, 10), # 40% prior
        ("OVERDUE_PAYMENT", "create_payment_link"): (6, 10),   # 60% prior
        ("OVERDUE_PAYMENT", "propose_payment_plan"): (7, 10),  # 70% prior
        ("BROKEN_PROMISE", "request_payment_commitment"): (5, 10), # 50% prior
        ("BROKEN_PROMISE", "propose_payment_plan"): (7, 10),       # 70% prior
        ("BROKEN_PROMISE", "create_payment_link"): (6, 10),        # 60% prior
        ("UNDERPAYMENT", "investigate_underpayment"): (9, 10),      # 90% prior
        ("UNDERPAYMENT", "create_payment_link"): (6, 10),          # 60% prior
    }
    
    prior_success, prior_total = priors.get((issue_type, action), (5, 10))
    
    feedbacks = db.query(InterventionFeedback).filter(
        InterventionFeedback.issue_type == issue_type,
        InterventionFeedback.action == action
    ).all()
    
    observed_total = len(feedbacks)
    observed_success = sum(1 for f in feedbacks if f.success)
    
    smoothed_rate = (prior_success + observed_success) / (prior_total + observed_total)
    
    return {
        "action": action,
        "issue_type": issue_type,
        "observed_trials": observed_total,
        "observed_successes": observed_success,
        "empirical_success_rate": round(smoothed_rate, 3),
        "confidence": "HIGH" if observed_total >= 10 else ("MEDIUM" if observed_total >= 3 else "PRIOR_DOMINATED")
    }

# =========================================================================
# Estimation & Financial Math Tools (Deterministic)
# =========================================================================

def estimate_action_outcome(
    issue_type: str,
    amount: float,
    days_overdue: int,
    segment: str,
    promise_reliability: float,
    action: str,
    empirical_boost: float = 0.0
) -> Dict[str, float]:
    """
    Deterministic estimation tool: Calculates P(natural) and P(action) for a given candidate action.
    """
    from .scoring import estimate_natural_recovery_probability, estimate_candidate_action_probability
    
    p_nat = estimate_natural_recovery_probability(issue_type, amount, days_overdue, segment, promise_reliability)
    p_act = estimate_candidate_action_probability(issue_type, amount, days_overdue, segment, promise_reliability, action, empirical_boost)
    
    return {
        "p_natural": p_nat,
        "p_action": p_act,
        "incremental_probability": max(0.0, round(p_act - p_nat, 3))
    }

def calculate_expected_incremental_recovery(
    amount: float,
    p_natural: float,
    p_action: float,
    cost_penalty: float = 0.0
) -> float:
    """
    Deterministic Financial Calculation:
    Expected Incremental Recovery = Amount at Risk * (P_action - P_natural) - Cost Penalty.
    Guaranteed >= 0.
    """
    incremental_p = max(0.0, p_action - p_natural)
    gross_recovery = amount * incremental_p
    net_recovery = max(0.0, gross_recovery - cost_penalty)
    return round(net_recovery, 2)

# =========================================================================
# Policy & Merchant Controls
# =========================================================================

def get_merchant_policy(db: Session) -> Dict[str, Any]:
    """
    Retrieves the merchant safety bounds and configured limits.
    """
    policy = db.query(PolicySettings).filter(PolicySettings.id == "default").first()
    if not policy:
        return {
            "auto_approve_threshold": 10000.0,
            "require_approval_threshold": 100000.0,
            "allowed_actions": ["retry_payment", "create_payment_link", "send_payment_reminder", "request_payment_commitment", "propose_payment_plan", "investigate_underpayment", "escalate_to_human", "do_nothing"],
            "daily_intervention_budget": 30,
            "intervention_cost_penalty": 50.0
        }
    
    try:
        allowed = json.loads(policy.allowed_actions)
    except Exception:
        allowed = []
        
    return {
        "auto_approve_threshold": policy.auto_approve_threshold,
        "require_approval_threshold": policy.require_approval_threshold,
        "allowed_actions": allowed,
        "daily_intervention_budget": policy.daily_intervention_budget,
        "intervention_cost_penalty": policy.intervention_cost_penalty
    }

def check_payment_status(db: Session, invoice_id: str) -> str:
    """
    Checks current ledger status of an invoice.
    """
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    return inv.status if inv else "UNKNOWN"

def record_recovery(
    db: Session,
    case_id: str,
    customer_id: str,
    invoice_id: Optional[str],
    action: str,
    amount_recovered: float,
    outcome: str,
    details: Optional[Dict[str, Any]] = None
) -> RecoveryTransaction:
    """
    Records an immutable transaction to the real Recovery Ledger.
    """
    txn = RecoveryTransaction(
        id=f"TXN-REC-{random.randint(10000, 99999)}",
        case_id=case_id,
        customer_id=customer_id,
        invoice_id=invoice_id,
        action=action,
        amount_recovered=amount_recovered,
        outcome=outcome,
        details=json.dumps(details or {}),
        timestamp=datetime.datetime.utcnow()
    )
    db.add(txn)
    db.commit()
    return txn

def escalate_to_human(db: Session, case_id: str, reason: str) -> Case:
    """
    Safely marks a case as ESCALATED for human intervention.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if case:
        case.status = "ESCALATED"
        case.recommended_action = "escalate_to_human"
        case.selected_action_reason = reason
        db.commit()
    return case
