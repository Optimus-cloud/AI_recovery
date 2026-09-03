from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
import datetime
import json

from .database import engine, Base, get_db
from .models import (
    Customer, Invoice, PaymentAttempt, Promise, AdjustmentRefund,
    Case, PolicySettings, AuditLog, RecoveryTransaction, InterventionFeedback
)
from .schemas import (
    CustomerSchema, CaseSchema, PolicySettingsSchema, PolicySettingsUpdate,
    ExecuteActionRequest, DashboardStats, AuditLogSchema, FeedbackStatsSchema
)
from .agent import scan_revenue_opportunities, execute_recovery_action
from .generator import generate_synthetic_data
from .evaluation import run_batch_evaluation
from .agent_tools import record_agent_event, get_intervention_success_rates

app = FastAPI(title="RazorResolve API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def serialize_case(case: Case, db: Session) -> CaseSchema:
    customer = db.query(Customer).filter(Customer.id == case.customer_id).first()
    
    # Parse candidate actions
    try:
        candidate_actions = json.loads(case.candidate_actions) if case.candidate_actions else []
    except Exception:
        candidate_actions = []
        
    # Parse decision trace
    try:
        decision_trace = json.loads(case.decision_trace) if case.decision_trace else []
    except Exception:
        decision_trace = []

    # Parse tools called
    try:
        tools_called = json.loads(case.investigation_tools_called) if case.investigation_tools_called else []
    except Exception:
        tools_called = []

    try:
        reasoning = json.loads(case.ai_reasoning) if case.ai_reasoning else []
    except Exception:
        reasoning = []

    try:
        audit = json.loads(case.audit_history) if case.audit_history else []
    except Exception:
        audit = []

    return CaseSchema(
        id=case.id,
        customer_id=case.customer_id,
        customer_name=customer.name if customer else "Unknown Customer",
        customer_segment=customer.segment if customer else "unknown",
        customer_reliability=f"{customer.payment_reliability:.0%}" if customer else "0%",
        invoice_id=case.invoice_id,
        issue_type=case.issue_type,
        amount_at_risk=case.amount_at_risk,
        status=case.status,
        priority=case.priority,
        p_natural=case.p_natural,
        p_intervene=case.p_intervene,
        expected_incremental_recovery=case.expected_incremental_recovery,
        recommended_action=case.recommended_action,
        selected_action_reason=case.selected_action_reason,
        candidate_actions=candidate_actions,
        decision_trace=decision_trace,
        investigation_tools_called=tools_called,
        budget_allocated=case.budget_allocated if case.budget_allocated is not None else True,
        ai_reasoning=reasoning,
        human_approval_required=case.human_approval_required,
        audit_history=audit,
        created_at=case.created_at,
        updated_at=case.updated_at
    )

# =========================================================================
# Core Opportunity & Case Routes
# =========================================================================

@app.get("/api/opportunities", response_model=List[CaseSchema])
def get_opportunities(status: Optional[str] = None, db: Session = Depends(get_db)):
    """Fetch opportunities, optional filtering by status."""
    query = db.query(Case)
    if status:
        query = query.filter(Case.status == status)
    cases = query.all()
    return [serialize_case(c, db) for c in cases]

@app.get("/api/cases/{case_id}", response_model=CaseSchema)
def get_case(case_id: str, db: Session = Depends(get_db)):
    """Fetch details of a specific case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return serialize_case(case, db)

@app.get("/api/cases/{case_id}/trace")
def get_case_trace(case_id: str, db: Session = Depends(get_db)):
    """Fetch the step-by-step 10-stage Agent Decision Trace for a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    try:
        trace = json.loads(case.decision_trace) if case.decision_trace else []
    except Exception:
        trace = []
    return {"case_id": case.id, "trace": trace}

@app.post("/api/cases/{case_id}/approve", response_model=CaseSchema)
def approve_case(case_id: str, db: Session = Depends(get_db)):
    """Approve a pending case action."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case.status = "OPEN"
    case.human_approval_required = False
    
    audit = json.loads(case.audit_history) if case.audit_history else []
    audit.append({
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "event": "HUMAN_APPROVED",
        "message": "Action approved by merchant. Ready for execution."
    })
    case.audit_history = json.dumps(audit)
    db.commit()
    
    record_agent_event(db, case_id, "ACTION_APPROVED", {"action": case.recommended_action})
    return serialize_case(case, db)

@app.post("/api/cases/{case_id}/execute", response_model=CaseSchema)
def execute_case_action(case_id: str, request: ExecuteActionRequest = None, db: Session = Depends(get_db)):
    """Execute action on a case."""
    custom_action = request.custom_action if request else None
    try:
        updated_case = execute_recovery_action(db, case_id, custom_action)
        return serialize_case(updated_case, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scan", response_model=List[CaseSchema])
def trigger_scan(db: Session = Depends(get_db)):
    """Trigger agent ledger scan."""
    cases = scan_revenue_opportunities(db)
    return [serialize_case(c, db) for c in cases]

@app.post("/api/seed")
def seed_database(db: Session = Depends(get_db)):
    """Regenerates the complete synthetic dataset using seed 42."""
    generate_synthetic_data(db)
    return {"message": "Synthetic ledger generated successfully."}

@app.post("/api/evaluate")
def evaluate_campaign(db: Session = Depends(get_db)):
    """Run matched counterfactual evaluation."""
    results = run_batch_evaluation(db, batch_size=100)
    return results

# =========================================================================
# Dashboard & Accounting Stats
# =========================================================================

@app.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Computes dashboard KPIs using real double-entry recovery ledger values.
    """
    total_at_risk = db.query(func.sum(Case.amount_at_risk)).filter(
        Case.status.in_(["OPEN", "PENDING_APPROVAL", "ESCALATED"])
    ).scalar() or 0.0
    
    potential_recoverable = db.query(func.sum(Case.expected_incremental_recovery)).filter(
        Case.status.in_(["OPEN", "PENDING_APPROVAL"])
    ).scalar() or 0.0
    
    high_priority_count = db.query(Case).filter(
        Case.priority.in_(["HIGH", "CRITICAL"]),
        Case.status.in_(["OPEN", "PENDING_APPROVAL"])
    ).count()

    # REAL RECOVERY LEDGER: Sum from RecoveryTransaction table
    revenue_recovered = db.query(func.sum(RecoveryTransaction.amount_recovered)).filter(
        RecoveryTransaction.outcome == "SUCCESS"
    ).scalar() or 0.0
    
    actions_executed_count = db.query(RecoveryTransaction).count()

    human_escalations = db.query(Case).filter(Case.status == "ESCALATED").count()
    
    # Policy Budget
    policy = db.query(PolicySettings).filter(PolicySettings.id == "default").first()
    daily_budget = policy.daily_intervention_budget if policy else 30
    used_budget = db.query(RecoveryTransaction).filter(RecoveryTransaction.action != "do_nothing").count()
    remaining_budget = max(0, daily_budget - used_budget)

    # Learning Feedback Rate
    total_feedbacks = db.query(InterventionFeedback).count()
    successful_feedbacks = db.query(InterventionFeedback).filter(InterventionFeedback.success == True).count()
    learned_rate = round(successful_feedbacks / total_feedbacks, 3) if total_feedbacks > 0 else 0.0

    # Leak breakdown
    breakdown = {
        "FAILED_PAYMENT": db.query(func.sum(Case.amount_at_risk)).filter(Case.issue_type == "FAILED_PAYMENT", Case.status.in_(["OPEN", "PENDING_APPROVAL"])).scalar() or 0.0,
        "OVERDUE_PAYMENT": db.query(func.sum(Case.amount_at_risk)).filter(Case.issue_type == "OVERDUE_PAYMENT", Case.status.in_(["OPEN", "PENDING_APPROVAL"])).scalar() or 0.0,
        "BROKEN_PROMISE": db.query(func.sum(Case.amount_at_risk)).filter(Case.issue_type == "BROKEN_PROMISE", Case.status.in_(["OPEN", "PENDING_APPROVAL"])).scalar() or 0.0,
        "UNDERPAYMENT": db.query(func.sum(Case.amount_at_risk)).filter(Case.issue_type == "UNDERPAYMENT", Case.status.in_(["OPEN", "PENDING_APPROVAL"])).scalar() or 0.0,
    }

    recovery_rate = round(revenue_recovered / max(1.0, revenue_recovered + total_at_risk) * 100, 2)

    return DashboardStats(
        total_at_risk=round(total_at_risk, 2),
        potential_recoverable=round(potential_recoverable, 2),
        high_priority_count=high_priority_count,
        actions_executed_count=actions_executed_count,
        revenue_recovered=round(revenue_recovered, 2),
        estimated_incremental=round(potential_recoverable, 2),
        recovery_rate=recovery_rate,
        human_escalations=human_escalations,
        daily_budget_total=daily_budget,
        daily_budget_remaining=remaining_budget,
        learned_success_rate=learned_rate,
        breakdown=breakdown
    )

# =========================================================================
# Policy Settings & Outcome Learning Stats
# =========================================================================

@app.get("/api/policies", response_model=PolicySettingsSchema)
def get_policies(db: Session = Depends(get_db)):
    policy = db.query(PolicySettings).filter(PolicySettings.id == "default").first()
    if not policy:
        raise HTTPException(status_code=404, detail="Default policy settings not found.")
    
    try:
        allowed = json.loads(policy.allowed_actions)
    except Exception:
        allowed = []

    return PolicySettingsSchema(
        auto_approve_threshold=policy.auto_approve_threshold,
        audit_log_threshold=policy.audit_log_threshold,
        require_approval_threshold=policy.require_approval_threshold,
        allowed_actions=allowed,
        max_discount_rate=policy.max_discount_rate,
        daily_limit=policy.daily_limit,
        daily_intervention_budget=policy.daily_intervention_budget or 30,
        intervention_cost_penalty=policy.intervention_cost_penalty or 50.0
    )

@app.put("/api/policies", response_model=PolicySettingsSchema)
def update_policies(update: PolicySettingsUpdate, db: Session = Depends(get_db)):
    policy = db.query(PolicySettings).filter(PolicySettings.id == "default").first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    if update.auto_approve_threshold is not None:
        policy.auto_approve_threshold = update.auto_approve_threshold
    if update.audit_log_threshold is not None:
        policy.audit_log_threshold = update.audit_log_threshold
    if update.require_approval_threshold is not None:
        policy.require_approval_threshold = update.require_approval_threshold
    if update.allowed_actions is not None:
        policy.allowed_actions = json.dumps(update.allowed_actions)
    if update.max_discount_rate is not None:
        policy.max_discount_rate = update.max_discount_rate
    if update.daily_limit is not None:
        policy.daily_limit = update.daily_limit
    if update.daily_intervention_budget is not None:
        policy.daily_intervention_budget = update.daily_intervention_budget
    if update.intervention_cost_penalty is not None:
        policy.intervention_cost_penalty = update.intervention_cost_penalty

    db.commit()
    record_agent_event(db, None, "POLICY_UPDATED", {"updated_fields": update.dict(exclude_unset=True)})
    return get_policies(db)

@app.get("/api/feedback/stats", response_model=FeedbackStatsSchema)
def get_feedback_stats(db: Session = Depends(get_db)):
    """Fetch statistical action success rates learned from past trials."""
    total = db.query(InterventionFeedback).count()
    succ = db.query(InterventionFeedback).filter(InterventionFeedback.success == True).count()
    overall = round(succ / total, 3) if total > 0 else 0.0

    actions = ["retry_payment", "create_payment_link", "send_payment_reminder", "request_payment_commitment", "propose_payment_plan", "investigate_underpayment"]
    by_action = {}
    for act in actions:
        rate_data = get_intervention_success_rates(db, "OVERDUE_PAYMENT", act)
        by_action[act] = rate_data

    return FeedbackStatsSchema(
        total_interventions=total,
        overall_success_rate=overall,
        by_action=by_action
    )

@app.get("/api/activity-feed", response_model=List[AuditLogSchema])
def get_activity_feed(db: Session = Depends(get_db)):
    """Fetch real backend agent events."""
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(50).all()
    
    result = []
    for l in logs:
        try:
            d = json.loads(l.details) if l.details else {}
        except Exception:
            d = {"raw": l.details}
            
        result.append(AuditLogSchema(
            id=l.id,
            timestamp=l.timestamp,
            case_id=l.case_id,
            action=l.action,
            details=d
        ))
    return result
