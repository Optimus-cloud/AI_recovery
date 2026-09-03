import datetime
import json
import random
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from .models import (
    Case, Invoice, PaymentAttempt, Promise, Customer, AdjustmentRefund,
    AuditLog, PolicySettings, RecoveryTransaction, InterventionFeedback
)
from .agent_tools import (
    record_agent_event, get_customer_profile, get_payment_history,
    get_promise_history, get_invoice_details, get_payment_attempts,
    get_refund_history, get_adjustment_history, investigate_underpayment as tool_investigate_underpayment,
    get_previous_interventions, get_intervention_success_rates, get_merchant_policy,
    record_recovery, estimate_action_outcome, calculate_expected_incremental_recovery,
    escalate_to_human
)
from .scoring import (
    calculate_promise_reliability,
    estimate_natural_recovery_probability,
    determine_priority,
    evaluate_all_candidate_actions
)
from .policy import check_policy
from .llm import agent_reason_and_select_action

def scan_revenue_opportunities(db: Session) -> list:
    """
    Autonomous Opportunity Scanner:
    Observes the ledger, identifies at-risk invoices, runs dynamic tool investigation,
    evaluates candidate actions, and allocates the daily intervention budget.
    """
    current_time = datetime.datetime(2026, 8, 30, 12, 0, 0)
    record_agent_event(db, None, "SCAN_STARTED", {"timestamp": current_time.isoformat(), "scope": "full_ledger"})

    # Fetch policy for budget constraints
    policy = db.query(PolicySettings).filter(PolicySettings.id == "default").first()
    daily_budget = policy.daily_intervention_budget if policy else 30
    
    new_cases_count = 0
    created_cases = []

    # 1. Failed Payments
    failed_attempts_sub = db.query(PaymentAttempt.invoice_id).filter(PaymentAttempt.status == "FAILED").subquery()
    success_attempts_sub = db.query(PaymentAttempt.invoice_id).filter(PaymentAttempt.status == "SUCCESS").subquery()

    failed_invoices = db.query(Invoice).filter(
        Invoice.status.in_(["UNPAID", "OVERDUE"]),
        Invoice.id.in_(failed_attempts_sub.select()),
        Invoice.id.not_in(success_attempts_sub.select())
    ).all()

    for inv in failed_invoices:
        case_id = f"REC-F{inv.id.split('-')[1]}"
        existing = db.query(Case).filter(Case.id == case_id).first()
        if not existing:
            c = investigate_and_create_case(db, case_id, inv.customer_id, inv.id, "FAILED_PAYMENT", inv.amount, current_time)
            if c:
                created_cases.append(c)
                new_cases_count += 1

    # 2. Overdue Payments
    overdue_invoices = db.query(Invoice).filter(
        Invoice.status == "OVERDUE",
        Invoice.id.not_in(failed_attempts_sub.select()),
        Invoice.id.not_in(success_attempts_sub.select())
    ).all()

    for inv in overdue_invoices:
        days_overdue = (current_time - inv.due_date).days
        if days_overdue >= 3:
            case_id = f"REC-O{inv.id.split('-')[1]}"
            existing = db.query(Case).filter(Case.id == case_id).first()
            if not existing:
                c = investigate_and_create_case(db, case_id, inv.customer_id, inv.id, "OVERDUE_PAYMENT", inv.amount, current_time)
                if c:
                    created_cases.append(c)
                    new_cases_count += 1

    # 3. Broken Promises
    broken_promises = db.query(Promise).filter(
        Promise.status == "BROKEN",
        Promise.promised_date < current_time
    ).all()

    for prm in broken_promises:
        inv = db.query(Invoice).filter(Invoice.id == prm.invoice_id).first()
        if inv and inv.status in ["UNPAID", "OVERDUE"]:
            case_id = f"REC-P{inv.id.split('-')[1]}"
            existing = db.query(Case).filter(Case.id == case_id).first()
            if not existing:
                c = investigate_and_create_case(db, case_id, inv.customer_id, inv.id, "BROKEN_PROMISE", inv.amount, current_time)
                if c:
                    created_cases.append(c)
                    new_cases_count += 1

    # 4. Underpayments
    partial_invoices = db.query(Invoice).filter(Invoice.status == "PARTIAL").all()
    for inv in partial_invoices:
        paid = db.query(PaymentAttempt.amount).filter(
            PaymentAttempt.invoice_id == inv.id,
            PaymentAttempt.status == "SUCCESS"
        ).scalar() or 0.0
        diff = round(inv.amount - paid, 2)
        if diff > 10.0:
            case_id = f"REC-U{inv.id.split('-')[1]}"
            existing = db.query(Case).filter(Case.id == case_id).first()
            if not existing:
                c = investigate_and_create_case(db, case_id, inv.customer_id, inv.id, "UNDERPAYMENT", diff, current_time)
                if c:
                    created_cases.append(c)
                    new_cases_count += 1

    # Apply Resource Budget Allocation
    all_open_cases = db.query(Case).filter(Case.status.in_(["OPEN", "PENDING_APPROVAL"])).all()
    all_open_cases.sort(key=lambda x: x.expected_incremental_recovery, reverse=True)
    
    allocated_count = 0
    for idx, c in enumerate(all_open_cases):
        if c.recommended_action != "do_nothing" and allocated_count < daily_budget:
            c.budget_allocated = True
            allocated_count += 1
        else:
            c.budget_allocated = (c.recommended_action == "do_nothing")

    db.commit()
    record_agent_event(db, None, "SCAN_COMPLETED", {
        "new_cases_count": new_cases_count,
        "total_active_cases": len(all_open_cases),
        "budget_allocated_count": allocated_count,
        "daily_budget": daily_budget
    })

    return all_open_cases


def run_agent_decision_pipeline(
    db: Session,
    customer_id: str,
    invoice_id: str,
    issue_type: str,
    amount_at_risk: float,
    current_time: datetime.datetime
) -> Dict[str, Any]:
    """
    Stateless Core Agent Decision Pipeline (Single Source of Truth):
    OBSERVE -> CHOOSE TOOLS -> RETRIEVE EVIDENCE -> GENERATE CANDIDATES ->
    ESTIMATE OUTCOMES DETERMINISTICALLY -> AI REASONING ACTION SELECTION -> POLICY CHECK.
    
    Does NOT depend on or mutate production Case records, ensuring clean evaluation isolation.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not customer or not invoice:
        raise ValueError(f"Customer {customer_id} or Invoice {invoice_id} not found.")

    tools_called = []
    
    # Tool 1: Profile & Invoice
    tools_called.append("get_customer_profile")
    cust_profile = get_customer_profile(db, customer_id)

    tools_called.append("get_invoice_details")
    inv_details = get_invoice_details(db, invoice_id)
    days_overdue = inv_details.get("days_overdue", 0) if inv_details else 5

    error_code = None
    underpayment_audit = None
    promise_reliability = customer.payment_reliability

    # Tool Invocations by Case Context
    if issue_type == "UNDERPAYMENT":
        tools_called.append("get_payment_history")
        payment_hist = get_payment_history(db, customer_id)
        
        tools_called.append("get_refund_history")
        refunds = get_refund_history(db, invoice_id)
        
        tools_called.append("get_adjustment_history")
        adjustments = get_adjustment_history(db, invoice_id)
        
        tools_called.append("investigate_underpayment")
        underpayment_audit = tool_investigate_underpayment(db, invoice_id)

    elif issue_type == "FAILED_PAYMENT":
        tools_called.append("get_payment_history")
        payment_hist = get_payment_history(db, customer_id)
        
        tools_called.append("get_payment_attempts")
        attempts = get_payment_attempts(db, invoice_id)
        error_code = attempts[0].get("error_code") if attempts else "unknown"

    elif issue_type == "BROKEN_PROMISE":
        tools_called.append("get_promise_history")
        promise_hist = get_promise_history(db, customer_id)
        promise_reliability = promise_hist.get("promise_reliability_score", 0.50)
        
        tools_called.append("get_previous_interventions")
        prev_interventions = get_previous_interventions(db, customer_id)
        
        tools_called.append("get_payment_history")
        payment_hist = get_payment_history(db, customer_id)

    else: # OVERDUE_PAYMENT
        tools_called.append("get_payment_history")
        payment_hist = get_payment_history(db, customer_id)
        
        tools_called.append("get_promise_history")
        promise_hist = get_promise_history(db, customer_id)
        promise_reliability = promise_hist.get("promise_reliability_score", 0.50)

    evidence_summary = {
        "days_overdue": days_overdue,
        "payment_success_rate": f"{payment_hist.get('success_rate', 1.0):.0%}",
        "promise_reliability": f"{promise_reliability:.0%}",
        "total_past_invoices": payment_hist.get("total_invoices", 1),
        "recent_error_code": error_code,
        "underpayment_status": underpayment_audit.get("investigation_status") if underpayment_audit else None,
        "underpayment_legit": underpayment_audit.get("is_legitimate_discount") if underpayment_audit else None
    }

    # Merchant Policy Settings
    policy_settings = get_merchant_policy(db)
    cost_penalty = policy_settings.get("intervention_cost_penalty", 50.0)
    allowed_actions = policy_settings.get("allowed_actions", [])

    # Candidate Actions & Deterministic Action Estimates
    candidate_actions, default_best = evaluate_all_candidate_actions(
        db=db,
        customer_id=customer_id,
        customer_segment=customer.segment,
        customer_reliability=customer.payment_reliability,
        issue_type=issue_type,
        amount_at_risk=amount_at_risk,
        days_overdue=days_overdue,
        promise_reliability=promise_reliability,
        cost_penalty=cost_penalty
    )

    # Agent Reasons over Evidence & Selects Action
    agent_decision = agent_reason_and_select_action(
        case_id=f"DEC-{invoice_id}",
        customer_name=customer.name,
        segment=customer.segment,
        reliability=customer.payment_reliability,
        issue_type=issue_type,
        amount=amount_at_risk,
        days_overdue=days_overdue,
        evidence=evidence_summary,
        candidate_estimates=candidate_actions,
        allowed_actions=allowed_actions
    )

    selected_action_key = agent_decision.get("selected_action", "create_payment_link")
    selected_reason = agent_decision.get("selected_reason", "Action maximizes expected incremental recovery.")
    reasoning_list = agent_decision.get("reasoning_points", [])

    for c in candidate_actions:
        c["selected"] = (c["action"] == selected_action_key)

    chosen_candidate = next((c for c in candidate_actions if c["action"] == selected_action_key), candidate_actions[0])

    # Policy Validation Check
    policy_res = check_policy(db, amount_at_risk, selected_action_key)
    human_approval = policy_res.get("approval_required", False)

    return {
        "customer": customer,
        "invoice": invoice,
        "issue_type": issue_type,
        "amount_at_risk": amount_at_risk,
        "days_overdue": days_overdue,
        "tools_called": tools_called,
        "evidence_summary": evidence_summary,
        "candidate_actions": candidate_actions,
        "selected_action": selected_action_key,
        "selected_reason": selected_reason,
        "reasoning_list": reasoning_list,
        "p_natural": chosen_candidate["p_natural"],
        "p_intervene": chosen_candidate["p_action"],
        "expected_incremental_recovery": chosen_candidate["expected_incremental_recovery"],
        "policy_res": policy_res,
        "human_approval_required": human_approval
    }


def investigate_and_create_case(
    db: Session,
    case_id: str,
    customer_id: str,
    invoice_id: str,
    issue_type: str,
    amount_at_risk: float,
    current_time: datetime.datetime
) -> Optional[Case]:
    """
    Core Production Case Creator:
    Calls run_agent_decision_pipeline, records trace and events to audit log, and creates Case record.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not customer or not invoice:
        return None

    record_agent_event(db, case_id, "CASE_IDENTIFIED", {
        "customer": customer.name,
        "amount": amount_at_risk,
        "issue_type": issue_type
    })

    # Run the genuine pipeline
    record_agent_event(db, case_id, "TOOL_CALL_STARTED", {"target": "customer_and_invoice_context"})
    res = run_agent_decision_pipeline(db, customer_id, invoice_id, issue_type, amount_at_risk, current_time)
    record_agent_event(db, case_id, "TOOL_CALL_COMPLETED", {"tools_invoked": res["tools_called"]})
    record_agent_event(db, case_id, "EVIDENCE_RETRIEVED", res["evidence_summary"])
    record_agent_event(db, case_id, "CANDIDATE_ACTIONS_GENERATED", {"issue_type": issue_type})
    record_agent_event(db, case_id, "ACTION_ESTIMATION_REQUESTED", {"candidate_count": len(res["candidate_actions"])})
    record_agent_event(db, case_id, "ACTION_ESTIMATE_RECEIVED", {
        "candidate_matrix": [{c["action"]: c["expected_incremental_recovery"]} for c in res["candidate_actions"]]
    })
    record_agent_event(db, case_id, "AGENT_DECISION", {
        "selected_action": res["selected_action"],
        "reason": res["selected_reason"],
        "expected_incremental": res["expected_incremental_recovery"]
    })

    policy_res = res["policy_res"]
    human_approval = res["human_approval_required"]
    selected_action_key = res["selected_action"]
    chosen_candidate = next((c for c in res["candidate_actions"] if c["action"] == selected_action_key), res["candidate_actions"][0])

    trace_steps = [
        {
            "step_number": 1,
            "stage": "CASE_IDENTIFIED",
            "title": "Revenue Leak Identified",
            "description": f"Agent observed potential revenue at risk of ₹{amount_at_risk:,.2f} on invoice {invoice_id} ({issue_type.replace('_', ' ')}).",
            "timestamp": current_time.isoformat(),
            "data": {"invoice_id": invoice_id, "amount_at_risk": amount_at_risk, "issue_type": issue_type}
        },
        {
            "step_number": 2,
            "stage": "INVESTIGATION_TOOLS_CALLED",
            "title": "Autonomous Tool Invocations",
            "description": f"Agent selected and invoked {len(res['tools_called'])} targeted tools: {', '.join([f'{t}()' for t in res['tools_called']])}.",
            "timestamp": current_time.isoformat(),
            "data": {"tools": res["tools_called"]}
        },
        {
            "step_number": 3,
            "stage": "EVIDENCE_EVALUATION",
            "title": "Evidence Synthesis",
            "description": f"Customer '{customer.name}' ({customer.segment.replace('_', ' ')}) overdue: {res['days_overdue']} days.",
            "timestamp": current_time.isoformat(),
            "data": res["evidence_summary"]
        },
        {
            "step_number": 4,
            "stage": "CANDIDATE_ACTIONS_EVALUATED",
            "title": "Counterfactual Candidate Action Evaluation",
            "description": f"Evaluated {len(res['candidate_actions'])} candidate actions against baseline P(natural) = {res['p_natural']:.0%}.",
            "timestamp": current_time.isoformat(),
            "data": {"candidate_matrix": res["candidate_actions"]}
        },
        {
            "step_number": 5,
            "stage": "DECISION_FINALIZED",
            "title": "Agent Action Selection",
            "description": res["selected_reason"],
            "timestamp": current_time.isoformat(),
            "data": {
                "recommended_action": selected_action_key,
                "incremental_recovery": res["expected_incremental_recovery"],
                "p_natural": res["p_natural"],
                "p_action": res["p_intervene"]
            }
        },
        {
            "step_number": 6,
            "stage": "POLICY_VERIFICATION",
            "title": "Merchant Policy & Guardrails Check",
            "description": f"Policy engine result: {policy_res.get('reason')}. Human authorization required: {human_approval}.",
            "timestamp": current_time.isoformat(),
            "data": policy_res
        }
    ]

    # Handle policy rejection
    if not policy_res.get("approved") and policy_res.get("escalate", False):
        record_agent_event(db, case_id, "POLICY_REJECTED", {"action": selected_action_key, "reason": policy_res.get("reason")})
        status = "ESCALATED"
        audit_initial = [
            {
                "timestamp": current_time.isoformat(),
                "event": "CASE_CREATED",
                "message": f"Autonomous case created for {issue_type} of ₹{amount_at_risk:,.2f}.",
                "details": {"action": selected_action_key, "expected_recovery": chosen_candidate["expected_incremental_recovery"]}
            },
            {
                "timestamp": current_time.isoformat(),
                "event": "AGENT_RECOMMENDATION_POLICY_REJECTED",
                "message": f"Policy rejected agent recommended action '{selected_action_key}': {policy_res.get('reason')}. Escalating to human desk.",
                "details": policy_res
            }
        ]
    else:
        record_agent_event(db, case_id, "POLICY_CHECK", {
            "action": selected_action_key,
            "approved": policy_res.get("approved"),
            "approval_required": human_approval
        })

        if human_approval:
            record_agent_event(db, case_id, "HUMAN_APPROVAL_REQUIRED", {
                "amount": amount_at_risk,
                "threshold": 100000.0
            })

        status = "OPEN"
        if selected_action_key == "do_nothing":
            status = "DO_NOTHING"
        elif human_approval:
            status = "PENDING_APPROVAL"
        elif policy_res.get("escalate", False):
            status = "ESCALATED"

        audit_initial = [
            {
                "timestamp": current_time.isoformat(),
                "event": "CASE_CREATED",
                "message": f"Autonomous case created for {issue_type} of ₹{amount_at_risk:,.2f}.",
                "details": {"action": selected_action_key, "expected_recovery": chosen_candidate["expected_incremental_recovery"]}
            }
        ]

    priority = determine_priority(chosen_candidate["expected_incremental_recovery"])

    new_case = Case(
        id=case_id,
        customer_id=customer_id,
        invoice_id=invoice_id,
        issue_type=issue_type,
        amount_at_risk=amount_at_risk,
        status=status,
        priority=priority,
        p_natural=chosen_candidate["p_natural"],
        p_intervene=chosen_candidate["p_action"],
        expected_incremental_recovery=chosen_candidate["expected_incremental_recovery"],
        recommended_action=selected_action_key,
        selected_action_reason=res["selected_reason"],
        candidate_actions=json.dumps(res["candidate_actions"]),
        decision_trace=json.dumps(trace_steps),
        investigation_tools_called=json.dumps(res["tools_called"]),
        budget_allocated=True,
        ai_reasoning=json.dumps(res["reasoning_list"]),
        human_approval_required=human_approval,
        audit_history=json.dumps(audit_initial),
        created_at=current_time
    )

    db.add(new_case)
    record_agent_event(db, case_id, "CASE_OPENED", {
        "customer": customer.name,
        "amount": amount_at_risk,
        "action": selected_action_key,
        "priority": priority,
        "expected_incremental": chosen_candidate["expected_incremental_recovery"]
    })

    return new_case


def execute_recovery_action(db: Session, case_id: str, custom_action: Optional[str] = None) -> Case:
    """
    Executes a recovery action through simulated transactional tools.
    Enforces policy checks, records double-entry transactions in RecoveryTransaction,
    and updates InterventionFeedback for Bayesian historical effectiveness learning.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise ValueError(f"Case {case_id} not found.")

    action = custom_action or case.recommended_action
    customer = db.query(Customer).filter(Customer.id == case.customer_id).first()
    invoice = db.query(Invoice).filter(Invoice.id == case.invoice_id).first()

    audit_trail = json.loads(case.audit_history) if case.audit_history else []
    trace_steps = json.loads(case.decision_trace) if case.decision_trace else []
    current_time = datetime.datetime.utcnow()

    # Policy Validation before execution
    policy_res = check_policy(db, case.amount_at_risk, action)
    if not policy_res["approved"] and policy_res.get("escalate", False) and action != "escalate_to_human":
        case.status = "ESCALATED"
        audit_trail.append({
            "timestamp": current_time.isoformat(),
            "event": "AGENT_RECOMMENDATION_POLICY_REJECTED",
            "message": f"Action '{action}' is blocked by merchant policy: {policy_res['reason']}. Escalating to human desk."
        })
        case.audit_history = json.dumps(audit_trail)
        db.commit()
        record_agent_event(db, case_id, "POLICY_REJECTED", {"action": action, "reason": policy_res["reason"]})
        return case

    record_agent_event(db, case_id, "ACTION_EXECUTED", {"action": action, "custom_override": custom_action is not None})

    trace_steps.append({
        "step_number": len(trace_steps) + 1,
        "stage": "ACTION_EXECUTED",
        "title": f"Executing Action: {action}",
        "description": f"Dispatched simulated recovery tool '{action}' for invoice {invoice.id if invoice else 'N/A'}.",
        "timestamp": current_time.isoformat(),
        "data": {"action": action, "custom_override": custom_action is not None}
    })

    # =========================================================================
    # TOOL: DO_NOTHING
    # =========================================================================
    if action == "do_nothing":
        case.status = "DO_NOTHING"
        audit_trail.append({
            "timestamp": current_time.isoformat(),
            "event": "ACTION_DO_NOTHING",
            "message": "Agent decided to Do Nothing: customer has high natural propensity to pay without intervention."
        })
        record_recovery(db, case_id, customer.id, invoice.id if invoice else None, "do_nothing", 0.0, "DO_NOTHING")
        case.audit_history = json.dumps(audit_trail)
        case.decision_trace = json.dumps(trace_steps)
        db.commit()
        record_agent_event(db, case_id, "OUTCOME_RECEIVED", {"outcome": "DO_NOTHING", "amount_recovered": 0.0})
        return case

    # =========================================================================
    # TOOL: INVESTIGATE_UNDERPAYMENT
    # =========================================================================
    if action == "investigate_underpayment":
        audit_result = tool_investigate_underpayment(db, case.invoice_id)
        if audit_result.get("is_legitimate_discount"):
            case.status = "IGNORED"
            case.amount_at_risk = 0.0
            case.expected_incremental_recovery = 0.0
            if invoice:
                invoice.status = "PAID"
                
            audit_trail.append({
                "timestamp": current_time.isoformat(),
                "event": "INVESTIGATION_RESOLVED",
                "message": f"Investigation complete. Legitimate co-marketing discount/credit of ₹{audit_result['total_adjustments']:,.2f} verified. Case resolved: Not Recoverable.",
                "details": audit_result
            })
            
            record_recovery(db, case_id, customer.id, invoice.id if invoice else None, "investigate_underpayment", 0.0, "NOT_RECOVERABLE", audit_result)
            feedback = InterventionFeedback(
                customer_id=customer.id,
                customer_segment=customer.segment,
                issue_type=case.issue_type,
                action="investigate_underpayment",
                amount=0.0,
                outcome="RESOLVED_LEGIT",
                success=True,
                time_to_payment_days=0
            )
            db.add(feedback)
            record_agent_event(db, case_id, "OUTCOME_RECEIVED", {"outcome": "NOT_RECOVERABLE", "status": "RESOLVED_LEGIT"})
            record_agent_event(db, case_id, "LEARNING_UPDATED", {"action": "investigate_underpayment", "success": True})
        else:
            case.status = "OPEN"
            case.recommended_action = "create_payment_link"
            case.p_natural = 0.15
            case.p_intervene = 0.68
            case.expected_incremental_recovery = round(case.amount_at_risk * (0.68 - 0.15), 2)
            case.priority = determine_priority(case.expected_incremental_recovery)
            
            audit_trail.append({
                "timestamp": current_time.isoformat(),
                "event": "INVESTIGATION_FAILED",
                "message": f"Investigation complete. Unreconciled gap of ₹{audit_result['unreconciled_leak']:,.2f} confirmed. Action updated to Payment Link.",
                "details": audit_result
            })
            record_agent_event(db, case_id, "OUTCOME_RECEIVED", {"outcome": "RECOVERABLE", "unreconciled_leak": audit_result['unreconciled_leak']})

        case.audit_history = json.dumps(audit_trail)
        case.decision_trace = json.dumps(trace_steps)
        db.commit()
        return case

    # =========================================================================
    # TOOL: ESCALATE_TO_HUMAN
    # =========================================================================
    if action == "escalate_to_human":
        case.status = "ESCALATED"
        audit_trail.append({
            "timestamp": current_time.isoformat(),
            "event": "ESCALATED_TO_HUMAN",
            "message": "Case escalated to manual operations desk for high-touch customer communication."
        })
        record_recovery(db, case_id, customer.id, invoice.id if invoice else None, "escalate_to_human", 0.0, "ESCALATED")
        feedback = InterventionFeedback(
            customer_id=customer.id,
            customer_segment=customer.segment,
            issue_type=case.issue_type,
            action="escalate_to_human",
            amount=case.amount_at_risk,
            outcome="ESCALATED",
            success=False,
            time_to_payment_days=0
        )
        db.add(feedback)
        case.audit_history = json.dumps(audit_trail)
        case.decision_trace = json.dumps(trace_steps)
        db.commit()
        record_agent_event(db, case_id, "OUTCOME_RECEIVED", {"outcome": "ESCALATED"})
        record_agent_event(db, case_id, "LEARNING_UPDATED", {"action": "escalate_to_human", "success": False})
        return case

    # =========================================================================
    # TRANSACTIONAL RECOVERY TOOLS (retry_payment, create_payment_link, etc.)
    # =========================================================================
    success_roll = random.random()
    is_success = success_roll <= case.p_intervene

    if is_success:
        case.status = "RECOVERED"
        if invoice:
            invoice.status = "PAID"
        recovered_amount = case.amount_at_risk

        attempt = PaymentAttempt(
            id=f"TXN-REC-{random.randint(10000, 99999)}",
            invoice_id=invoice.id if invoice else "INV-MOCK",
            amount=recovered_amount,
            status="SUCCESS",
            created_at=current_time
        )
        db.add(attempt)

        txn = record_recovery(
            db=db,
            case_id=case_id,
            customer_id=customer.id,
            invoice_id=invoice.id if invoice else None,
            action=action,
            amount_recovered=recovered_amount,
            outcome="SUCCESS",
            details={"roll": round(success_roll, 3), "p_threshold": case.p_intervene}
        )

        feedback = InterventionFeedback(
            customer_id=customer.id,
            customer_segment=customer.segment,
            issue_type=case.issue_type,
            action=action,
            amount=recovered_amount,
            outcome="SUCCESS",
            success=True,
            time_to_payment_days=random.randint(1, 4)
        )
        db.add(feedback)

        audit_trail.append({
            "timestamp": current_time.isoformat(),
            "event": "RECOVERY_SUCCESS",
            "message": f"Simulated payment of ₹{recovered_amount:,.2f} RECEIVED successfully via {action}.",
            "details": {"transaction_id": txn.id, "amount": recovered_amount}
        })

        trace_steps.append({
            "step_number": len(trace_steps) + 1,
            "stage": "RECOVERY_LOGGED",
            "title": "Revenue Recovered & Ledger Updated",
            "description": f"Recorded actual recovered revenue of ₹{recovered_amount:,.2f} under transaction ID {txn.id}.",
            "timestamp": current_time.isoformat(),
            "data": {"transaction_id": txn.id, "amount_recovered": recovered_amount, "outcome": "SUCCESS"}
        })

        record_agent_event(db, case_id, "OUTCOME_RECEIVED", {"outcome": "SUCCESS", "amount": recovered_amount})
        record_agent_event(db, case_id, "RECOVERY_RECORDED", {"transaction_id": txn.id, "amount": recovered_amount, "action": action})
        record_agent_event(db, case_id, "LEARNING_UPDATED", {"action": action, "success": True, "observed_time_days": feedback.time_to_payment_days})

    else:
        is_timeout = success_roll > case.p_intervene and success_roll <= (case.p_intervene + 0.20)
        outcome = "TIMEOUT" if is_timeout else "DECLINED"
        case.status = "FAILED"

        txn = record_recovery(
            db=db,
            case_id=case_id,
            customer_id=customer.id,
            invoice_id=invoice.id if invoice else None,
            action=action,
            amount_recovered=0.0,
            outcome=outcome,
            details={"roll": round(success_roll, 3), "p_threshold": case.p_intervene}
        )

        feedback = InterventionFeedback(
            customer_id=customer.id,
            customer_segment=customer.segment,
            issue_type=case.issue_type,
            action=action,
            amount=case.amount_at_risk,
            outcome=outcome,
            success=False,
            time_to_payment_days=0
        )
        db.add(feedback)

        audit_trail.append({
            "timestamp": current_time.isoformat(),
            "event": f"RECOVERY_{outcome}",
            "message": f"Simulated intervention outcome: {outcome.lower()}.",
            "details": {"transaction_id": txn.id}
        })

        trace_steps.append({
            "step_number": len(trace_steps) + 1,
            "stage": "RECOVERY_LOGGED",
            "title": f"Outcome Observed: {outcome}",
            "description": f"Intervention did not yield payment. Outcome recorded in recovery ledger and learning history.",
            "timestamp": current_time.isoformat(),
            "data": {"transaction_id": txn.id, "amount_recovered": 0.0, "outcome": outcome}
        })

        record_agent_event(db, case_id, "OUTCOME_RECEIVED", {"outcome": outcome, "amount": 0.0})
        record_agent_event(db, case_id, "RECOVERY_RECORDED", {"transaction_id": txn.id, "amount": 0.0, "outcome": outcome})
        record_agent_event(db, case_id, "LEARNING_UPDATED", {"action": action, "success": False})

    case.audit_history = json.dumps(audit_trail)
    case.decision_trace = json.dumps(trace_steps)
    db.commit()
    return case
