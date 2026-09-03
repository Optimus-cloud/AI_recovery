from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CustomerSchema(BaseModel):
    id: str
    name: str
    email: str
    segment: str
    payment_reliability: float
    created_at: datetime

    class Config:
        from_attributes = True

class CandidateActionSchema(BaseModel):
    action: str
    label: str
    p_natural: float
    p_action: float
    expected_incremental_recovery: float
    intervention_cost: float
    policy_permitted: bool
    policy_reason: Optional[str] = None
    rank: int
    selected: bool

class DecisionTraceStepSchema(BaseModel):
    step_number: int
    stage: str
    title: str
    description: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None

class CaseSchema(BaseModel):
    id: str
    customer_id: str
    customer_name: Optional[str] = None
    customer_segment: Optional[str] = None
    customer_reliability: Optional[str] = None
    invoice_id: Optional[str] = None
    issue_type: str
    amount_at_risk: float
    status: str
    priority: str
    p_natural: float
    p_intervene: float
    expected_incremental_recovery: float
    recommended_action: str
    selected_action_reason: Optional[str] = None
    candidate_actions: List[CandidateActionSchema] = []
    decision_trace: List[DecisionTraceStepSchema] = []
    investigation_tools_called: List[str] = []
    budget_allocated: bool = True
    ai_reasoning: List[str]
    human_approval_required: bool
    audit_history: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class RecoveryTransactionSchema(BaseModel):
    id: str
    case_id: Optional[str] = None
    customer_id: str
    invoice_id: Optional[str] = None
    action: str
    amount_recovered: float
    outcome: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class PolicySettingsSchema(BaseModel):
    auto_approve_threshold: float
    audit_log_threshold: float
    require_approval_threshold: float
    allowed_actions: List[str]
    max_discount_rate: float
    daily_limit: int
    daily_intervention_budget: int = 30
    intervention_cost_penalty: float = 50.0

    class Config:
        from_attributes = True

class PolicySettingsUpdate(BaseModel):
    auto_approve_threshold: Optional[float] = None
    audit_log_threshold: Optional[float] = None
    require_approval_threshold: Optional[float] = None
    allowed_actions: Optional[List[str]] = None
    max_discount_rate: Optional[float] = None
    daily_limit: Optional[int] = None
    daily_intervention_budget: Optional[int] = None
    intervention_cost_penalty: Optional[float] = None

class ExecuteActionRequest(BaseModel):
    custom_action: Optional[str] = None

class DashboardStats(BaseModel):
    total_at_risk: float
    potential_recoverable: float
    high_priority_count: int
    actions_executed_count: int
    revenue_recovered: float
    estimated_incremental: float
    recovery_rate: float
    human_escalations: int
    daily_budget_total: int = 30
    daily_budget_remaining: int = 30
    learned_success_rate: float = 0.0
    breakdown: Dict[str, float]

class AuditLogSchema(BaseModel):
    id: int
    timestamp: datetime
    case_id: Optional[str]
    action: str
    details: Dict[str, Any]

    class Config:
        from_attributes = True

class FeedbackStatsSchema(BaseModel):
    total_interventions: int
    overall_success_rate: float
    by_action: Dict[str, Dict[str, Any]]
