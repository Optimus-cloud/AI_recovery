from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from .database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    segment = Column(String, nullable=False)  # reliable, occasional_late, chronic_late, broken_promise, partial_payer
    payment_reliability = Column(Float, default=1.0)  # General payment success rate (0-1)
    
    # Latent behavioral characteristics (Ground Truth discovered through tool investigation)
    natural_pay_propensity = Column(Float, default=0.50)
    link_responsiveness = Column(Float, default=0.60)
    reminder_responsiveness = Column(Float, default=0.40)
    plan_responsiveness = Column(Float, default=0.70)
    avg_delay_days = Column(Integer, default=5)
    true_promise_reliability = Column(Float, default=0.50)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    invoices = relationship("Invoice", back_populates="customer")
    promises = relationship("Promise", back_populates="customer")
    cases = relationship("Case", back_populates="customer")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # PAID, UNPAID, OVERDUE, PARTIAL
    due_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="invoices")
    attempts = relationship("PaymentAttempt", back_populates="invoice")
    promises = relationship("Promise", back_populates="invoice")
    adjustments = relationship("AdjustmentRefund", back_populates="invoice")
    cases = relationship("Case", back_populates="invoice")

class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id = Column(String, primary_key=True, index=True)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # SUCCESS, FAILED, PENDING
    error_code = Column(String, nullable=True)  # insufficient_funds, network_error, expired_card
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    invoice = relationship("Invoice", back_populates="attempts")

class Promise(Base):
    __tablename__ = "promises"

    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    promised_amount = Column(Float, nullable=False)
    promised_date = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)  # KEPT, BROKEN, PENDING
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="promises")
    invoice = relationship("Invoice", back_populates="promises")

class AdjustmentRefund(Base):
    __tablename__ = "adjustments_refunds"

    id = Column(String, primary_key=True, index=True)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # REFUND, DISCOUNT, FEE_ADJUSTMENT
    reason = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    invoice = relationship("Invoice", back_populates="adjustments")

class Case(Base):
    __tablename__ = "cases"

    id = Column(String, primary_key=True, index=True)  # REC-XXXXX
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=True)
    issue_type = Column(String, nullable=False)  # FAILED_PAYMENT, OVERDUE_PAYMENT, BROKEN_PROMISE, UNDERPAYMENT
    amount_at_risk = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # OPEN, PENDING_APPROVAL, EXECUTED, RECOVERED, IGNORED, ESCALATED, FAILED, DO_NOTHING
    priority = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    p_natural = Column(Float, nullable=False)
    p_intervene = Column(Float, nullable=False)
    expected_incremental_recovery = Column(Float, nullable=False)
    recommended_action = Column(String, nullable=False)  # DO_NOTHING, RETRY_PAYMENT, SEND_PAYMENT_LINK, SEND_REMINDER, REQUEST_PAYMENT_COMMITMENT, PROPOSE_PAYMENT_PLAN, ESCALATE_TO_HUMAN, INVESTIGATE_UNDERPAYMENT
    selected_action_reason = Column(Text, nullable=True)
    
    # Agentic V2 Features
    candidate_actions = Column(Text, default="[]")  # JSON-serialized list of evaluated candidate actions
    decision_trace = Column(Text, default="[]")     # JSON-serialized list of 10-step agent execution trace
    investigation_tools_called = Column(Text, default="[]") # JSON-serialized list of tool names invoked
    budget_allocated = Column(Boolean, default=True) # Whether allocated in daily intervention budget
    
    ai_reasoning = Column(Text, nullable=False)  # JSON-serialized list of strings
    human_approval_required = Column(Boolean, default=False)
    audit_history = Column(Text, nullable=False)  # JSON-serialized list of events
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    customer = relationship("Customer", back_populates="cases")
    invoice = relationship("Invoice", back_populates="cases")

class RecoveryTransaction(Base):
    """
    Real Recovery Ledger: Tracks every simulated actual recovery transaction.
    TOTAL REVENUE RECOVERED = SUM(amount_recovered) where outcome == 'SUCCESS'.
    """
    __tablename__ = "recovery_transactions"

    id = Column(String, primary_key=True, index=True) # TXN-REC-XXXXX
    case_id = Column(String, ForeignKey("cases.id"), nullable=True)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    invoice_id = Column(String, ForeignKey("invoices.id"), nullable=True)
    action = Column(String, nullable=False)
    amount_recovered = Column(Float, default=0.0)
    outcome = Column(String, nullable=False) # SUCCESS, TIMEOUT, DECLINED, NOT_RECOVERABLE, ESCALATED, DO_NOTHING
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(Text, nullable=True) # JSON details

class InterventionFeedback(Base):
    """
    Outcome Learning & Feedback Record:
    Stores historical intervention outcomes to compute empirical action effectiveness.
    """
    __tablename__ = "intervention_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, nullable=False)
    customer_segment = Column(String, nullable=False)
    issue_type = Column(String, nullable=False)
    action = Column(String, nullable=False)
    amount = Column(Float, default=0.0)
    outcome = Column(String, nullable=False) # SUCCESS, FAILED, TIMEOUT, RESOLVED_LEGIT
    success = Column(Boolean, default=False)
    time_to_payment_days = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class PolicySettings(Base):
    __tablename__ = "policy_settings"

    id = Column(String, primary_key=True, default="default")
    auto_approve_threshold = Column(Float, default=10000.0)
    audit_log_threshold = Column(Float, default=10000.0)
    require_approval_threshold = Column(Float, default=100000.0)
    allowed_actions = Column(Text, default="[]")  # JSON-serialized list
    max_discount_rate = Column(Float, default=0.15)
    daily_limit = Column(Integer, default=50)
    daily_intervention_budget = Column(Integer, default=30) # Max high-touch interventions per day
    intervention_cost_penalty = Column(Float, default=50.0) # Opportunity cost per contact

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    case_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    details = Column(Text, nullable=True)
