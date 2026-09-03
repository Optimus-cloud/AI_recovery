import math
import json
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from .models import Promise, Customer, PolicySettings
from .policy import check_policy

def calculate_promise_reliability(db: Session, customer_id: str) -> float:
    """
    Calculate the reliability score of a customer based on past Promise-to-Pay records.
    R_promise = Kept Promises / Total Completed Promises
    """
    promises = db.query(Promise).filter(
        Promise.customer_id == customer_id,
        Promise.status.in_(["KEPT", "BROKEN"])
    ).all()
    
    if not promises:
        return 0.50  # Neutral baseline
        
    kept = sum(1 for p in promises if p.status == "KEPT")
    total = len(promises)
    return round(kept / total, 2)

def estimate_natural_recovery_probability(
    issue_type: str,
    amount: float,
    days_overdue: int,
    segment: str,
    promise_reliability: float
) -> float:
    """
    Estimate the probability of payment WITHOUT any intervention (P_natural).
    Answers: 'If I do nothing, what is likely to happen?'
    """
    segment_bases = {
        "reliable": 0.95,
        "occasional_late": 0.70,
        "chronic_late": 0.25,
        "broken_promise": 0.15,
        "partial_payer": 0.40
    }
    p_base = segment_bases.get(segment, 0.50)

    if issue_type == "FAILED_PAYMENT":
        # Technical failures rarely self-cure unless the user voluntarily tries again
        p_natural = p_base * 0.25
    elif issue_type == "OVERDUE_PAYMENT":
        # Exponential time decay: e^(-0.03 * days)
        decay = math.exp(-0.03 * max(0, days_overdue))
        p_natural = p_base * decay
    elif issue_type == "BROKEN_PROMISE":
        # Heavy penalty on broken commitments
        decay = math.exp(-0.04 * max(0, days_overdue))
        p_natural = p_base * max(0.1, promise_reliability) * decay
    elif issue_type == "UNDERPAYMENT":
        p_natural = p_base * 0.20
    else:
        p_natural = p_base

    return max(0.01, min(0.99, round(p_natural, 2)))

def estimate_candidate_action_probability(
    issue_type: str,
    amount: float,
    days_overdue: int,
    segment: str,
    promise_reliability: float,
    action: str,
    empirical_boost: float = 0.0
) -> float:
    """
    Estimate the probability of payment WITH a specific candidate action (P_action).
    """
    p_natural = estimate_natural_recovery_probability(issue_type, amount, days_overdue, segment, promise_reliability)

    if action == "do_nothing":
        return p_natural

    # Effectiveness factors by action
    action_multipliers = {
        "retry_payment": 0.82 if issue_type == "FAILED_PAYMENT" else 0.15,
        "create_payment_link": 0.68,
        "send_payment_reminder": 0.38,
        "request_payment_commitment": 0.52,
        "propose_payment_plan": 0.76,
        "investigate_underpayment": 0.92 if issue_type == "UNDERPAYMENT" else 0.10,
        "escalate_to_human": 0.85
    }
    
    boost = action_multipliers.get(action, 0.30)
    if empirical_boost > 0:
        # Blend empirical historical rate with domain model
        boost = 0.6 * boost + 0.4 * empirical_boost

    segment_responsiveness = {
        "reliable": 0.95,
        "occasional_late": 0.82,
        "chronic_late": 0.58,
        "broken_promise": 0.48,
        "partial_payer": 0.72
    }
    responsiveness = segment_responsiveness.get(segment, 0.60)
    
    p_action = p_natural + (1.0 - p_natural) * boost * responsiveness
    
    if issue_type == "BROKEN_PROMISE" and action in ["request_payment_commitment", "propose_payment_plan"]:
        p_action = p_natural + (p_action - p_natural) * (0.4 + 0.6 * promise_reliability)

    return max(p_natural, min(0.99, round(p_action, 2)))

def calculate_expected_incremental_recovery(
    amount: float,
    p_natural: float,
    p_action: float,
    cost_penalty: float = 0.0
) -> float:
    """
    Expected Incremental Recovery = Amount at Risk * (P_action - P_natural) - Cost Penalty
    Guaranteed >= 0.
    """
    incremental_p = max(0.0, p_action - p_natural)
    gross_recovery = amount * incremental_p
    net_recovery = max(0.0, gross_recovery - cost_penalty)
    return round(net_recovery, 2)

def determine_priority(expected_incremental_recovery: float) -> str:
    """
    Prioritize opportunities based on EXPECTED INCREMENTAL RECOVERY (not just raw balance).
    """
    if expected_incremental_recovery >= 100000:
        return "CRITICAL"
    elif expected_incremental_recovery >= 30000:
        return "HIGH"
    elif expected_incremental_recovery >= 5000:
        return "MEDIUM"
    else:
        return "LOW"

def evaluate_all_candidate_actions(
    db: Session,
    customer_id: str,
    customer_segment: str,
    customer_reliability: float,
    issue_type: str,
    amount_at_risk: float,
    days_overdue: int,
    promise_reliability: float,
    cost_penalty: float = 50.0
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Candidate Action Evaluation Engine:
    Evaluates ALL candidate actions for a case, computes counterfactual P(natural) vs P(action),
    checks merchant policy compliance, and selects the optimal action.
    """
    from .agent_tools import get_intervention_success_rates
    
    candidate_list = [
        ("do_nothing", "Do Nothing (Natural Self-Recovery)"),
        ("send_payment_reminder", "Send Soft Payment Reminder"),
        ("create_payment_link", "Send Instant UPI/Card Payment Link"),
        ("retry_payment", "Retry Automated Payment Charge"),
        ("request_payment_commitment", "Request Promise-to-Pay Commitment"),
        ("propose_payment_plan", "Propose 3-Month Installment Plan"),
        ("investigate_underpayment", "Investigate Ledger Adjustments & Credits"),
        ("escalate_to_human", "Escalate to Human Operations Team")
    ]
    
    # Filter candidates by issue type relevance
    if issue_type == "FAILED_PAYMENT":
        relevant_actions = ["do_nothing", "retry_payment", "create_payment_link", "send_payment_reminder", "escalate_to_human"]
    elif issue_type == "UNDERPAYMENT":
        relevant_actions = ["do_nothing", "investigate_underpayment", "create_payment_link", "send_payment_reminder", "escalate_to_human"]
    elif issue_type == "BROKEN_PROMISE":
        relevant_actions = ["do_nothing", "create_payment_link", "propose_payment_plan", "request_payment_commitment", "escalate_to_human"]
    else: # OVERDUE_PAYMENT
        relevant_actions = ["do_nothing", "send_payment_reminder", "create_payment_link", "propose_payment_plan", "escalate_to_human"]

    p_natural = estimate_natural_recovery_probability(
        issue_type, amount_at_risk, days_overdue, customer_segment, promise_reliability
    )
    
    evaluated_actions = []
    
    for action_key, label in candidate_list:
        if action_key not in relevant_actions:
            continue
            
        # Empirical rate lookup
        empirical_data = get_intervention_success_rates(db, issue_type, action_key)
        empirical_boost = empirical_data.get("empirical_success_rate", 0.0)
        
        p_action = estimate_candidate_action_probability(
            issue_type, amount_at_risk, days_overdue, customer_segment, promise_reliability, action_key, empirical_boost
        )
        
        action_cost = 0.0 if action_key == "do_nothing" else cost_penalty
        exp_incremental = calculate_expected_incremental_recovery(
            amount_at_risk, p_natural, p_action, action_cost
        )
        
        # Policy verification
        policy_res = check_policy(db, amount_at_risk, action_key)
        policy_permitted = policy_res.get("approved", False) or (policy_res.get("approval_required", False) and not policy_res.get("escalate", False))
        
        evaluated_actions.append({
            "action": action_key,
            "label": label,
            "p_natural": p_natural,
            "p_action": p_action,
            "expected_incremental_recovery": exp_incremental,
            "intervention_cost": action_cost,
            "policy_permitted": policy_permitted,
            "policy_reason": policy_res.get("reason", "Permitted under standard guidelines"),
            "rank": 0,
            "selected": False
        })
        
    # Sort by Expected Incremental Recovery descending
    evaluated_actions.sort(key=lambda x: (x["policy_permitted"], x["expected_incremental_recovery"]), reverse=True)
    
    for rank, act in enumerate(evaluated_actions, start=1):
        act["rank"] = rank
        
    # Top selection logic:
    # If natural recovery is very high (>= 90%) and incremental gain is negligible (< 1000), choose DO_NOTHING
    best_action = evaluated_actions[0]
    
    if p_natural >= 0.90 and best_action["expected_incremental_recovery"] < 1000.0:
        # Find do_nothing
        do_nothing_act = next((a for a in evaluated_actions if a["action"] == "do_nothing"), None)
        if do_nothing_act:
            best_action = do_nothing_act
            
    best_action["selected"] = True
    
    return evaluated_actions, best_action
