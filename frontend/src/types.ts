export interface CandidateAction {
  action: string;
  label: string;
  p_natural: number;
  p_action: number;
  expected_incremental_recovery: number;
  intervention_cost: number;
  policy_permitted: boolean;
  policy_reason?: string;
  rank: number;
  selected: boolean;
}

export interface DecisionTraceStep {
  step_number: number;
  stage: string;
  title: string;
  description: string;
  timestamp: string;
  data?: any;
}

export interface Case {
  id: string;
  customer_id: string;
  customer_name: string;
  customer_segment: string;
  customer_reliability: string;
  invoice_id?: string;
  issue_type: string;
  amount_at_risk: number;
  status: 'OPEN' | 'PENDING_APPROVAL' | 'EXECUTED' | 'RECOVERED' | 'IGNORED' | 'ESCALATED' | 'FAILED' | 'DO_NOTHING';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  p_natural: number;
  p_intervene: number;
  expected_incremental_recovery: number;
  recommended_action: string;
  selected_action_reason?: string;
  candidate_actions: CandidateAction[];
  decision_trace: DecisionTraceStep[];
  investigation_tools_called: string[];
  budget_allocated: boolean;
  ai_reasoning: string[];
  human_approval_required: boolean;
  audit_history: {
    timestamp: string;
    event: string;
    message: string;
    details?: any;
  }[];
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  total_at_risk: number;
  potential_recoverable: number;
  high_priority_count: number;
  actions_executed_count: number;
  revenue_recovered: number;
  estimated_incremental: number;
  recovery_rate: number;
  human_escalations: number;
  daily_budget_total: number;
  daily_budget_remaining: number;
  learned_success_rate: number;
  breakdown: {
    FAILED_PAYMENT: number;
    OVERDUE_PAYMENT: number;
    BROKEN_PROMISE: number;
    UNDERPAYMENT: number;
  };
}

export interface PolicySettings {
  auto_approve_threshold: number;
  audit_log_threshold: number;
  require_approval_threshold: number;
  allowed_actions: string[];
  max_discount_rate: number;
  daily_limit: number;
  daily_intervention_budget: number;
  intervention_cost_penalty: number;
}

export interface AuditLogEntry {
  id: number;
  timestamp: string;
  case_id?: string;
  action: string;
  details: any;
}

export interface EvaluationResults {
  summary: {
    total_at_risk: number;
    baseline: {
      recovered: number;
      recovery_rate: number;
      interventions: number;
      roi: number;
      unnecessary_interventions: number;
      false_recoveries: number;
    };
    ai: {
      recovered: number;
      recovery_rate: number;
      interventions: number;
      roi: number;
      unnecessary_interventions: number;
      false_recoveries: number;
      escalations: number;
      do_nothing_count: number;
    };
    metrics: {
      incremental_recovered: number;
      improvement_pct: number;
    };
  };
  cases: {
    invoice_id: string;
    customer: string;
    segment: string;
    issue_type: string;
    amount_at_risk: number;
    p_natural: number;
    baseline: {
      action: string;
      p_effective: number;
      recovered: number;
    };
    ai: {
      action: string;
      p_effective: number;
      recovered: number;
    };
    incremental_gain: number;
  }[];
}
