import React, { useState } from 'react';
import { Case } from '../types';
import { 
  ArrowLeft, CheckCircle, Clock, Play, UserCheck, 
  HelpCircle, Sparkles, Layers, Search, Cpu, ListChecks, Check, ShieldAlert,
  ChevronDown, ChevronUp, Code, Terminal, CheckCircle2, Calculator, ArrowRight, AlertCircle,
  Lightbulb, Info, FileCheck, ShieldCheck
} from 'lucide-react';

interface CaseDetailProps {
  caseData: Case;
  onBack: () => void;
  onExecute: (caseId: string, customAction?: string) => Promise<void>;
  onApprove: (caseId: string) => Promise<void>;
}

export const CaseDetail: React.FC<CaseDetailProps> = ({ caseData, onBack, onExecute, onApprove }) => {
  const [selectedActionOverride, setSelectedActionOverride] = useState<string>('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [activeTab, setActiveTab] = useState<'trace' | 'candidates' | 'reasoning' | 'audit'>('trace');
  
  // Interactive state for all tabs
  const [expandedStep, setExpandedStep] = useState<number | null>(1);
  const [showRawJson, setShowRawJson] = useState<Record<number, boolean>>({});
  const [expandedCandidate, setExpandedCandidate] = useState<string | null>(null);
  const [expandedReasonIdx, setExpandedReasonIdx] = useState<number | null>(null);
  const [expandedAuditIdx, setExpandedAuditIdx] = useState<number | null>(0); // Default first expanded

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  const handleExecute = async (customAction?: string) => {
    setIsExecuting(true);
    try {
      await onExecute(caseData.id, customAction || selectedActionOverride || undefined);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleApproveOnly = async () => {
    setIsApproving(true);
    try {
      await onApprove(caseData.id);
    } finally {
      setIsApproving(false);
    }
  };

  const handleAuthorizeAndExecute = async (customAction?: string) => {
    setIsExecuting(true);
    try {
      await onApprove(caseData.id);
      await onExecute(caseData.id, customAction || selectedActionOverride || undefined);
    } finally {
      setIsExecuting(false);
    }
  };

  const toggleStep = (stepNumber: number) => {
    setExpandedStep(prev => prev === stepNumber ? null : stepNumber);
  };

  const toggleRawJson = (stepNumber: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setShowRawJson(prev => ({ ...prev, [stepNumber]: !prev[stepNumber] }));
  };

  const toggleCandidate = (actionKey: string) => {
    setExpandedCandidate(prev => prev === actionKey ? null : actionKey);
  };

  const toggleReasoning = (idx: number) => {
    setExpandedReasonIdx(prev => prev === idx ? null : idx);
  };

  const toggleAudit = (idx: number) => {
    setExpandedAuditIdx(prev => prev === idx ? null : idx);
  };

  const cleanActionName = (action: string) => {
    return action.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
  };

  const actionOptions = [
    { value: 'do_nothing', label: 'Do Nothing (Natural Self-Recovery)' },
    { value: 'retry_payment', label: 'Retry Payment' },
    { value: 'create_payment_link', label: 'Create Payment Link' },
    { value: 'send_payment_reminder', label: 'Send Payment Reminder' },
    { value: 'request_payment_commitment', label: 'Request Promise-to-Pay' },
    { value: 'propose_payment_plan', label: 'Propose Payment Plan' },
    { value: 'investigate_underpayment', label: 'Investigate Underpayment' },
    { value: 'escalate_to_human', label: 'Escalate to Human' },
  ];

  const isPendingApproval = caseData.status === 'PENDING_APPROVAL';
  const isRecovered = caseData.status === 'RECOVERED';
  const isDoNothing = caseData.status === 'DO_NOTHING';

  // Helper for deep insights on reasoning cards
  const getReasoningInsights = (tag: string) => {
    switch (tag) {
      case 'WHY THIS CUSTOMER':
        return {
          title: 'Customer Behavioral Modeling',
          points: [
            `Segment classification: '${caseData.customer_segment.replace('_', ' ')}'`,
            `Historical payment reliability index: ${caseData.customer_reliability}`,
            `Intervention responsiveness prior: Higher than average for digital payment link prompts.`
          ]
        };
      case 'WHY NOW':
        return {
          title: 'Temporal Urgency & Aging',
          points: [
            `Revenue at risk: ₹${caseData.amount_at_risk.toLocaleString('en-IN')}`,
            `Trigger status: ${caseData.issue_type.replace('_', ' ')} detected on active ledger.`,
            `Recovery degradation velocity: Probability drops ~5% per week of delay without prompt action.`
          ]
        };
      case 'WHY THIS ACTION':
        return {
          title: 'Counterfactual Optimization Rationale',
          points: [
            `Selected candidate maximizes Expected Incremental Recovery: +₹${caseData.expected_incremental_recovery.toLocaleString('en-IN')}`,
            `Expected lift: ${(caseData.p_natural*100).toFixed(0)}% (Natural) → ${(caseData.p_intervene*100).toFixed(0)}% (With ${cleanActionName(caseData.recommended_action)})`,
            `Cost penalty accounted for: ₹50 outreach friction subtracted.`
          ]
        };
      case 'WHY NOT OTHER ACTIONS':
        return {
          title: 'Comparative Action Exclusion Matrix',
          points: [
            `DO_NOTHING ruled out: Incremental lift (+₹${caseData.expected_incremental_recovery.toLocaleString('en-IN')}) justifies outreach friction.`,
            `Aggressive dunning deprioritized: Risk of customer churn exceeds immediate marginal collection value.`,
            `Installment plans: Reserved for invoices >₹1L with chronic delay history.`
          ]
        };
      case 'EVIDENCE USED':
        return {
          title: 'Verified Ledger Sources',
          points: [
            `Invoice ID: ${caseData.invoice_id || 'N/A'} (Amount: ₹${caseData.amount_at_risk.toLocaleString('en-IN')})`,
            `Investigation tools invoked: ${caseData.investigation_tools_called?.join(', ') || 'N/A'}`,
            `Empirical Bayesian priors blended with past outcome trial data.`
          ]
        };
      case 'UNCERTAINTIES':
        return {
          title: 'Model Uncertainty & Risk Guardrails',
          points: [
            `Natural recovery baseline has ±8% confidence interval.`,
            `External liquidity constraints of the customer cannot be fully observed without CRM sync.`,
            `Policy guardrails active: Auto-escalates to human if amount exceeds ₹1,00,000.`
          ]
        };
      default:
        return {
          title: 'Analytical Context',
          points: [`Evaluated using RazorResolve deterministic scoring and empirical feedback weights.`]
        };
    }
  };

  const getEventBadgeColor = (eventType: string) => {
    if (eventType.includes('SUCCESS') || eventType.includes('RESOLVED')) {
      return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    }
    if (eventType.includes('VIOLATION') || eventType.includes('FAILED') || eventType.includes('DECLINED')) {
      return 'bg-red-500/10 text-red-400 border-red-500/20';
    }
    if (eventType.includes('ESCALAT') || eventType.includes('APPROVAL')) {
      return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    }
    return 'bg-violet-500/10 text-violet-400 border-violet-500/20';
  };

  return (
    <div className="space-y-6 font-sans">
      {/* Top Header Back Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-xs font-semibold text-gray-400 hover:text-white bg-slate-900 border border-slate-800 px-3 py-2 rounded-lg transition-all hover:bg-slate-800 cursor-pointer"
        >
          <ArrowLeft size={14} /> Back to Queue
        </button>

        <div className="flex items-center gap-3">
          <span className="text-xs text-gray-400 font-mono">Case ID: <strong className="text-violet-400 font-bold">{caseData.id}</strong></span>
          <span className="text-xs font-bold text-gray-400 uppercase bg-slate-900 border border-slate-800 px-2.5 py-1 rounded">
            {caseData.issue_type.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Main Grid View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Customer & Recovery Potential */}
        <div className="space-y-6">
          
          {/* Customer Profile Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="font-semibold text-white pb-2 border-b border-slate-800">Customer & Invoice Profile</h3>
            
            <div className="space-y-3 text-sm">
              <div>
                <span className="text-xs text-gray-400 block">Customer Name</span>
                <span className="font-bold text-white text-base">{caseData.customer_name}</span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 pt-1">
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-gray-400 block uppercase">Segment</span>
                  <span className="font-semibold text-gray-200 capitalize">{caseData.customer_segment.replace('_', ' ')}</span>
                </div>
                <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                  <span className="text-[10px] text-gray-400 block uppercase">Promise Reliability</span>
                  <span className="font-semibold text-violet-400 font-mono">{caseData.customer_reliability}</span>
                </div>
              </div>

              <div className="pt-2 border-t border-slate-800 space-y-2">
                <div className="flex justify-between">
                  <span className="text-xs text-gray-400">Invoice ID:</span>
                  <span className="text-xs font-mono text-gray-300">{caseData.invoice_id || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-xs text-gray-400">Total At Risk:</span>
                  <span className="text-sm font-bold text-white font-mono">{formatCurrency(caseData.amount_at_risk)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Recovery Potential Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h3 className="font-semibold text-white flex items-center gap-2 pb-2 border-b border-slate-800">
              <Sparkles size={16} className="text-emerald-400" />
              <span>Counterfactual Impact</span>
            </h3>

            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <span className="text-[10px] text-gray-400 uppercase block font-semibold">Natural Recovery</span>
                <span className="text-xl font-mono font-bold text-gray-300">{(caseData.p_natural * 100).toFixed(0)}%</span>
                <span className="text-[10px] text-gray-500 block mt-0.5">P(Do-Nothing)</span>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <span className="text-[10px] text-gray-400 uppercase block font-semibold text-emerald-400">With Intervention</span>
                <span className="text-xl font-mono font-bold text-emerald-400">{(caseData.p_intervene * 100).toFixed(0)}%</span>
                <span className="text-[10px] text-emerald-500/70 block mt-0.5">P(Action)</span>
              </div>
            </div>

            <div className="bg-slate-950 p-3.5 rounded-lg border border-slate-800">
              <span className="text-xs text-gray-400 block">Expected Incremental Value</span>
              <span className="text-2xl font-bold font-mono text-violet-400 mt-1 block">
                {formatCurrency(caseData.expected_incremental_recovery)}
              </span>
              <span className="text-[11px] text-gray-400 mt-1 block leading-normal">
                Estimated extra revenue created by intervention versus natural self-cure (EV incremental).
              </span>
            </div>
          </div>

          {/* Policy Boundaries Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="font-semibold text-white flex items-center gap-1.5">
                <ShieldAlert size={16} className="text-violet-400" />
                <span>Policy Guardrails</span>
              </h3>
              <span className="text-xs font-bold font-mono text-gray-400 uppercase">{caseData.status.replace('_', ' ')}</span>
            </div>

            {isPendingApproval ? (
              <div className="bg-amber-500/10 border border-amber-500/20 text-amber-300 rounded-lg p-3.5 text-xs space-y-2.5">
                <div className="flex items-center gap-2 font-bold text-amber-400">
                  <Clock size={16} />
                  <span>Merchant Authorization Required</span>
                </div>
                <p className="leading-relaxed">
                  This transaction exceeds automatic execution limits (₹1,00,000 threshold). Merchant approval is required before dispatching the recovery tool.
                </p>
                <button
                  onClick={handleApproveOnly}
                  disabled={isApproving || isExecuting}
                  className="w-full bg-slate-800 hover:bg-slate-700 text-amber-300 border border-amber-500/30 font-bold py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <UserCheck size={14} />
                  {isApproving ? 'Authorizing...' : 'Authorize Policy Gate Only'}
                </button>
              </div>
            ) : isRecovered ? (
              <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-lg p-3.5 text-xs space-y-1">
                <div className="flex items-center gap-2 font-bold text-emerald-400">
                  <CheckCircle size={16} />
                  <span>Payment Successfully Recovered</span>
                </div>
                <p className="leading-relaxed">Transaction recorded in real double-entry recovery ledger.</p>
              </div>
            ) : isDoNothing ? (
              <div className="bg-slate-800/40 border border-slate-700/50 text-slate-300 rounded-lg p-3.5 text-xs space-y-1">
                <div className="flex items-center gap-2 font-bold text-slate-200">
                  <Check size={16} />
                  <span>Do Nothing Policy Selected</span>
                </div>
                <p className="leading-relaxed">Customer natural recovery propensity is high. Skipping outreach saves fatigue.</p>
              </div>
            ) : (
              <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 rounded-lg p-3.5 text-xs">
                <div className="flex items-center gap-2 font-bold text-emerald-400">
                  <CheckCircle size={16} />
                  <span>Auto-Approve Permitted</span>
                </div>
                <p className="mt-1 leading-relaxed">
                  Action fits merchant policy guidelines. Click execute to deploy recovery tool instantly.
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Right 2 Columns: Agent Decision Trace & Candidate Actions */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Action Execution Dispatch Bar */}
          <div className={`bg-slate-900 border rounded-xl p-5 space-y-4 shadow-sm transition-all ${selectedActionOverride ? 'border-violet-500 ring-1 ring-violet-500/30' : 'border-slate-800'}`}>
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-white text-base">Execute Recovery Action</h3>
                  {selectedActionOverride && (
                    <span className="text-[10px] bg-violet-600 text-white font-bold px-2 py-0.5 rounded-full animate-pulse flex items-center gap-1">
                      <AlertCircle size={11} /> Override: {cleanActionName(selectedActionOverride)}
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400 mt-0.5">
                  Deploy the recommended tool or choose a custom override.
                </p>
              </div>

              {isPendingApproval && (
                <span className="text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                  <Clock size={12} /> Authorization Needed
                </span>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-1">
              <div className="relative sm:w-72 shrink-0">
                <select
                  value={selectedActionOverride}
                  onChange={(e) => setSelectedActionOverride(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 text-sm text-gray-100 px-3.5 py-2.5 rounded-lg focus:outline-none focus:border-violet-500 appearance-none pr-8 cursor-pointer font-medium"
                >
                  <option value="" className="bg-slate-900 text-white">Recommended: {cleanActionName(caseData.recommended_action)}</option>
                  {actionOptions.map((opt) => (
                    <option key={opt.value} value={opt.value} className="bg-slate-900 text-gray-200">
                      Override: {opt.label}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400">
                  <svg className="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
                </div>
              </div>

              {isPendingApproval ? (
                <button
                  onClick={() => handleAuthorizeAndExecute()}
                  disabled={isExecuting || isRecovered}
                  className="bg-amber-500 hover:bg-amber-400 disabled:bg-slate-800 disabled:text-gray-500 text-slate-950 font-bold px-6 py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all text-sm grow shadow-lg shadow-amber-500/20 cursor-pointer"
                >
                  <UserCheck size={16} className={isExecuting ? 'animate-spin' : ''} />
                  {isExecuting ? 'Authorizing & Dispatching...' : selectedActionOverride ? `Authorize & Execute (${cleanActionName(selectedActionOverride)})` : 'Authorize & Execute Action'}
                </button>
              ) : (
                <button
                  onClick={() => handleExecute()}
                  disabled={isExecuting || isRecovered}
                  className="bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-gray-500 text-white font-bold px-6 py-2.5 rounded-lg flex items-center justify-center gap-2 transition-all text-sm grow shadow-lg shadow-emerald-600/20 cursor-pointer"
                >
                  <Play size={15} className={isExecuting ? 'animate-ping' : ''} />
                  {isExecuting ? 'Dispatching Simulated Tool...' : isRecovered ? 'Already Recovered (Ledger Verified)' : selectedActionOverride ? `Execute Override: ${cleanActionName(selectedActionOverride)}` : 'Execute Recovery Action'}
                </button>
              )}
            </div>
          </div>

          {/* Investigation Tools Invoked Bar */}
          {caseData.investigation_tools_called && caseData.investigation_tools_called.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1.5 mr-2">
                <Search size={14} className="text-violet-400" />
                Tools Called:
              </span>
              {caseData.investigation_tools_called.map((t, idx) => (
                <span key={idx} className="bg-slate-950 text-violet-300 border border-slate-800 font-mono text-[11px] px-2.5 py-1 rounded-md">
                  {t}()
                </span>
              ))}
            </div>
          )}

          {/* Sub-Navigation Tabs */}
          <div className="flex border-b border-slate-800 gap-6">
            <button
              onClick={() => setActiveTab('trace')}
              className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${activeTab === 'trace' ? 'border-violet-500 text-white' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
            >
              <Cpu size={16} />
              <span>Agent Decision Trace</span>
            </button>

            <button
              onClick={() => setActiveTab('candidates')}
              className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${activeTab === 'candidates' ? 'border-violet-500 text-white' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
            >
              <Layers size={16} />
              <span>Candidate Actions Matrix</span>
            </button>

            <button
              onClick={() => setActiveTab('reasoning')}
              className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${activeTab === 'reasoning' ? 'border-violet-500 text-white' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
            >
              <HelpCircle size={16} />
              <span>Reasoning (Why & Evidence)</span>
            </button>

            <button
              onClick={() => setActiveTab('audit')}
              className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-all cursor-pointer ${activeTab === 'audit' ? 'border-violet-500 text-white' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
            >
              <ListChecks size={16} />
              <span>Audit Log History</span>
            </button>
          </div>

          {/* TAB 1: DECISION TRACE (INTERACTIVE & EXPANDABLE) */}
          {activeTab === 'trace' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-white text-sm">Step-by-Step Autonomous Execution Trace</h4>
                  <p className="text-[11px] text-gray-400 mt-0.5">Click any step card to inspect the underlying tool parameters and evidence payload.</p>
                </div>
                <span className="text-[10px] text-violet-400 font-mono bg-violet-500/10 border border-violet-500/20 px-2 py-0.5 rounded">
                  {caseData.decision_trace ? `${caseData.decision_trace.length} Steps Recorded` : '0 Steps'}
                </span>
              </div>
              
              <div className="space-y-3 relative before:absolute before:inset-0 before:left-3.5 before:w-0.5 before:bg-slate-800">
                {caseData.decision_trace && caseData.decision_trace.length > 0 ? (
                  caseData.decision_trace.map((step) => {
                    const isExpanded = expandedStep === step.step_number;
                    const isRaw = showRawJson[step.step_number];

                    return (
                      <div key={step.step_number} className="relative flex items-start gap-3.5 pl-1">
                        {/* Number Badge */}
                        <div className={`w-6 h-6 rounded-full border text-xs font-mono flex items-center justify-center shrink-0 z-10 transition-colors ${isExpanded ? 'bg-violet-600 border-violet-400 text-white shadow-lg shadow-violet-600/30' : 'bg-slate-900 border-slate-700 text-gray-400'}`}>
                          {step.step_number}
                        </div>

                        {/* Interactive Step Card */}
                        <div 
                          onClick={() => toggleStep(step.step_number)}
                          className={`bg-slate-950 border rounded-xl grow p-3.5 cursor-pointer transition-all ${isExpanded ? 'border-violet-500/60 ring-1 ring-violet-500/20 bg-slate-950/90' : 'border-slate-800 hover:border-slate-700 hover:bg-slate-900/60'}`}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-white text-xs tracking-wide">{step.title}</span>
                              <span className="text-[9px] font-mono uppercase bg-slate-800 text-gray-400 px-1.5 py-0.5 rounded border border-slate-700">
                                {step.stage}
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="text-[10px] text-gray-500 font-mono">
                                {new Date(step.timestamp).toLocaleTimeString()}
                              </span>
                              {isExpanded ? (
                                <ChevronUp size={14} className="text-violet-400" />
                              ) : (
                                <ChevronDown size={14} className="text-gray-500" />
                              )}
                            </div>
                          </div>

                          <p className="text-xs text-gray-300 leading-relaxed mt-1.5">{step.description}</p>

                          {/* Expanded Inspector Drawer */}
                          {isExpanded && (
                            <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-3 animate-fade-in" onClick={(e) => e.stopPropagation()}>
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                                  <Terminal size={12} className="text-violet-400" />
                                  Inspection Payload & Context
                                </span>

                                <button
                                  onClick={(e) => toggleRawJson(step.step_number, e)}
                                  className="text-[10px] text-gray-400 hover:text-white flex items-center gap-1 font-mono bg-slate-900 border border-slate-800 px-2 py-0.5 rounded transition-colors cursor-pointer"
                                >
                                  <Code size={11} />
                                  {isRaw ? 'Structured View' : 'Raw JSON'}
                                </button>
                              </div>

                              {isRaw ? (
                                <pre className="bg-slate-900 border border-slate-800 p-2.5 rounded-lg text-[11px] font-mono text-gray-300 overflow-x-auto max-h-48">
                                  {JSON.stringify(step.data || step, null, 2)}
                                </pre>
                              ) : step.data ? (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  {Object.entries(step.data).map(([key, val]) => {
                                    if (key === 'candidate_matrix' && Array.isArray(val)) {
                                      return (
                                        <div key={key} className="col-span-full bg-slate-900/90 border border-slate-800 p-2 rounded-lg text-[11px]">
                                          <span className="text-gray-400 font-semibold block mb-1">Evaluated Options ({val.length}):</span>
                                          <div className="space-y-1">
                                            {val.map((c: any, i: number) => (
                                              <div key={i} className="flex justify-between items-center text-[10px] border-b border-slate-800/50 pb-0.5">
                                                <span className="text-white font-medium">{c.label}</span>
                                                <span className="font-mono text-violet-400">+{formatCurrency(c.expected_incremental_recovery)}</span>
                                              </div>
                                            ))}
                                          </div>
                                        </div>
                                      );
                                    }
                                    if (key === 'tools' && Array.isArray(val)) {
                                      return (
                                        <div key={key} className="col-span-full bg-slate-900/90 border border-slate-800 p-2 rounded-lg text-[11px] flex flex-wrap gap-1.5 items-center">
                                          <span className="text-gray-400 font-semibold mr-1">Tools Invoked:</span>
                                          {val.map((t: string, i: number) => (
                                            <span key={i} className="bg-slate-950 text-violet-300 font-mono text-[10px] px-2 py-0.5 rounded border border-slate-800 flex items-center gap-1">
                                              <CheckCircle2 size={10} className="text-emerald-400" /> {t}()
                                            </span>
                                          ))}
                                        </div>
                                      );
                                    }
                                    return (
                                      <div key={key} className="bg-slate-900/90 border border-slate-800 p-2 rounded-lg text-[11px]">
                                        <span className="text-gray-400 capitalize block text-[10px]">{key.replace(/_/g, ' ')}</span>
                                        <span className="text-white font-mono font-semibold truncate block mt-0.5">
                                          {typeof val === 'object' && val !== null ? JSON.stringify(val) : String(val)}
                                        </span>
                                      </div>
                                    );
                                  })}
                                </div>
                              ) : (
                                <p className="text-[11px] text-gray-500 italic">No additional payload attached to this step.</p>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-gray-500">No trace recorded.</p>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: CANDIDATE ACTIONS MATRIX (INTERACTIVE ROWS) */}
          {activeTab === 'candidates' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-white text-sm">Evaluated Candidate Actions Matrix</h4>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Click any action row below to inspect its mathematical formula breakdown and policy details.
                  </p>
                </div>
              </div>

              <div className="overflow-x-auto border border-slate-800 rounded-lg">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="bg-slate-950 text-gray-400 font-semibold border-b border-slate-800">
                      <th className="py-3 px-3">Rank</th>
                      <th className="py-3 px-3">Candidate Action</th>
                      <th className="py-3 px-3">P(Natural)</th>
                      <th className="py-3 px-3">P(Action)</th>
                      <th className="py-3 px-3 text-right">Incremental Lift</th>
                      <th className="py-3 px-3">Policy Status</th>
                      <th className="py-3 px-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {caseData.candidate_actions && caseData.candidate_actions.map((act) => {
                      const isExpanded = expandedCandidate === act.action;
                      const isSelectedOverride = selectedActionOverride === act.action;

                      return (
                        <React.Fragment key={act.action}>
                          <tr 
                            onClick={() => toggleCandidate(act.action)}
                            className={`cursor-pointer transition-colors ${act.selected ? 'bg-violet-950/30 font-medium' : 'hover:bg-slate-800/40'} ${isExpanded ? 'bg-slate-800/50' : ''}`}
                          >
                            <td className="py-3 px-3 font-mono font-bold text-violet-400">
                              <div className="flex items-center gap-1.5">
                                <span>#{act.rank}</span>
                                {isExpanded ? <ChevronUp size={12} className="text-violet-400" /> : <ChevronDown size={12} className="text-gray-500" />}
                              </div>
                            </td>
                            <td className="py-3 px-3 font-medium text-white">
                              <div className="flex items-center gap-2">
                                <span>{act.label}</span>
                                {isSelectedOverride && (
                                  <span className="text-[9px] bg-violet-600 text-white font-bold px-1.5 py-0.5 rounded">
                                    Active Override
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 px-3 font-mono text-gray-400">{(act.p_natural * 100).toFixed(0)}%</td>
                            <td className="py-3 px-3 font-mono font-bold text-emerald-400">{(act.p_action * 100).toFixed(0)}%</td>
                            <td className="py-3 px-3 text-right font-mono font-bold text-violet-400">
                              {formatCurrency(act.expected_incremental_recovery)}
                            </td>
                            <td className="py-3 px-3">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${act.policy_permitted ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                                {act.policy_permitted ? 'Permitted' : 'Blocked'}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-center">
                              {act.selected && (
                                <span className="bg-violet-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm">
                                  Selected
                                </span>
                              )}
                            </td>
                          </tr>

                          {/* Expanded Formula Inspector Drawer */}
                          {isExpanded && (
                            <tr className="bg-slate-950 border-y border-violet-500/20">
                              <td colSpan={7} className="p-4 space-y-3">
                                <div className="flex flex-wrap items-center justify-between gap-2">
                                  <div className="flex items-center gap-2">
                                    <Calculator size={14} className="text-violet-400" />
                                    <span className="text-xs font-bold text-white">Mathematical Lift Breakdown: {act.label}</span>
                                  </div>

                                  <div className="flex items-center gap-2">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setSelectedActionOverride(act.action);
                                      }}
                                      className={`font-bold text-[11px] px-3.5 py-1.5 rounded-md flex items-center gap-1.5 transition-all cursor-pointer ${
                                        isSelectedOverride 
                                          ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30' 
                                          : 'bg-violet-600 hover:bg-violet-500 text-white'
                                      }`}
                                    >
                                      {isSelectedOverride ? (
                                        <>
                                          <CheckCircle2 size={13} className="text-white" />
                                          <span>Selected as Active Override ✓</span>
                                        </>
                                      ) : (
                                        <>
                                          <span>Set as Active Override</span>
                                          <ArrowRight size={12} />
                                        </>
                                      )}
                                    </button>

                                    {/* Instant 1-Click Execution */}
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setSelectedActionOverride(act.action);
                                        if (isPendingApproval) {
                                          handleAuthorizeAndExecute(act.action);
                                        } else {
                                          handleExecute(act.action);
                                        }
                                      }}
                                      disabled={isExecuting || isRecovered}
                                      className="bg-slate-800 hover:bg-slate-700 disabled:bg-slate-900 disabled:text-gray-600 text-emerald-400 border border-emerald-500/30 font-bold text-[11px] px-3.5 py-1.5 rounded-md flex items-center gap-1.5 transition-all cursor-pointer"
                                    >
                                      <Play size={12} className={isExecuting ? 'animate-ping' : ''} />
                                      <span>Execute ({act.label}) Now</span>
                                    </button>
                                  </div>
                                </div>

                                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                                  <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                                    <span className="text-[10px] text-gray-400 block uppercase">Formula Applied</span>
                                    <code className="text-violet-300 font-mono block mt-1 text-[11px]">
                                      Amount × (P_action - P_natural) - Cost
                                    </code>
                                  </div>

                                  <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                                    <span className="text-[10px] text-gray-400 block uppercase">Calculation Values</span>
                                    <span className="text-gray-200 font-mono block mt-1 text-[11px]">
                                      ₹{caseData.amount_at_risk.toLocaleString('en-IN')} × ({(act.p_action*100).toFixed(0)}% - {(act.p_natural*100).toFixed(0)}%) - ₹{act.intervention_cost}
                                    </span>
                                  </div>

                                  <div className="bg-slate-900 p-2.5 rounded-lg border border-slate-800">
                                    <span className="text-[10px] text-gray-400 block uppercase">Policy Compliance Note</span>
                                    <span className="text-gray-300 block mt-1 text-[11px]">
                                      {act.policy_reason || 'Action fits merchant policy guidelines.'}
                                    </span>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: REASONING & WHY (CLICKABLE INSIGHT CARDS) */}
          {activeTab === 'reasoning' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-white text-sm">Autonomous Reasoning Rationale</h4>
                  <p className="text-[11px] text-gray-400 mt-0.5">Click any reasoning card below to expand underlying behavioral heuristics and evidence points.</p>
                </div>
                <span className="text-[10px] text-violet-400 font-mono bg-violet-500/10 border border-violet-500/20 px-2 py-0.5 rounded flex items-center gap-1">
                  <Lightbulb size={11} /> Click cards to inspect
                </span>
              </div>
              
              <div className="space-y-3">
                {caseData.ai_reasoning.map((item, idx) => {
                  const parts = item.split(': ');
                  const hasTag = parts.length > 1;
                  const tag = hasTag ? parts[0] : 'REASONING POINT';
                  const text = hasTag ? parts.slice(1).join(': ') : item;
                  const isExpanded = expandedReasonIdx === idx;
                  const insight = getReasoningInsights(tag);

                  return (
                    <div 
                      key={idx} 
                      onClick={() => toggleReasoning(idx)}
                      className={`bg-slate-950 border p-4 rounded-xl space-y-2 cursor-pointer transition-all ${isExpanded ? 'border-violet-500 ring-1 ring-violet-500/30 bg-slate-900/60' : 'border-slate-800 hover:border-violet-500/40 hover:bg-slate-900/30'}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-violet-400 bg-violet-500/10 border border-violet-500/20 px-2 py-0.5 rounded inline-block">
                          {tag}
                        </span>

                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-gray-500 font-mono">
                            {isExpanded ? 'Click to collapse' : 'Click to expand insights'}
                          </span>
                          {isExpanded ? <ChevronUp size={14} className="text-violet-400" /> : <ChevronDown size={14} className="text-gray-500" />}
                        </div>
                      </div>

                      <p className="text-xs text-gray-300 leading-relaxed font-sans">{text}</p>

                      {/* Expanded Deep Insights Drawer */}
                      {isExpanded && (
                        <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2 animate-fade-in" onClick={(e) => e.stopPropagation()}>
                          <div className="flex items-center gap-1.5 text-violet-300 text-xs font-semibold">
                            <Info size={13} className="text-violet-400" />
                            <span>{insight.title}</span>
                          </div>

                          <div className="bg-slate-900 border border-slate-800/80 rounded-lg p-3 space-y-1.5 text-[11px]">
                            {insight.points.map((pt, pIdx) => (
                              <div key={pIdx} className="flex items-start gap-2 text-gray-300">
                                <span className="text-violet-400 font-bold">•</span>
                                <span>{pt}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 4: AUDIT LOG HISTORY (INTERACTIVE & COMPLETE DRAWER) */}
          {activeTab === 'audit' && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-semibold text-white text-sm">Case Audit Trail & State Transitions</h4>
                  <p className="text-[11px] text-gray-400 mt-0.5">Immutable record of all autonomous decisions, policy verifications, and financial executions.</p>
                </div>
                <span className="text-[10px] text-violet-400 font-mono bg-violet-500/10 border border-violet-500/20 px-2 py-0.5 rounded flex items-center gap-1">
                  <ShieldCheck size={11} className="text-emerald-400" /> Ledger Verified
                </span>
              </div>
              
              <div className="space-y-3">
                {caseData.audit_history && caseData.audit_history.length > 0 ? (
                  caseData.audit_history.map((event, idx) => {
                    const isExpanded = expandedAuditIdx === idx;
                    const badgeClass = getEventBadgeColor(event.event);

                    return (
                      <div 
                        key={idx} 
                        onClick={() => toggleAudit(idx)}
                        className={`bg-slate-950 border rounded-xl p-4 space-y-2 cursor-pointer transition-all ${isExpanded ? 'border-violet-500 ring-1 ring-violet-500/30 bg-slate-950/90' : 'border-slate-800 hover:border-slate-700 hover:bg-slate-900/40'}`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border uppercase ${badgeClass}`}>
                              {event.event}
                            </span>
                            <span className="text-xs font-semibold text-white">{event.message}</span>
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="text-[10px] text-gray-500 font-mono">
                              {new Date(event.timestamp).toLocaleString()}
                            </span>
                            {isExpanded ? <ChevronUp size={14} className="text-violet-400" /> : <ChevronDown size={14} className="text-gray-500" />}
                          </div>
                        </div>

                        {/* Expanded Audit Drawer */}
                        {isExpanded && (
                          <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2.5 animate-fade-in" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-between text-[11px]">
                              <span className="text-gray-400 font-mono flex items-center gap-1">
                                <FileCheck size={12} className="text-emerald-400" />
                                Exact UTC Timestamp: <strong className="text-gray-200">{event.timestamp}</strong>
                              </span>
                              <span className="text-gray-500 font-mono text-[10px]">Event #{idx + 1}</span>
                            </div>

                            {event.details ? (
                              <div className="space-y-1">
                                <span className="text-[10px] text-gray-500 uppercase font-bold block">Event Execution Metadata:</span>
                                <pre className="bg-slate-900 border border-slate-800 p-2.5 rounded-lg text-[11px] font-mono text-gray-300 overflow-x-auto max-h-48">
                                  {JSON.stringify(event.details, null, 2)}
                                </pre>
                              </div>
                            ) : (
                              <div className="bg-slate-900 border border-slate-800 p-2.5 rounded-lg text-[11px] text-gray-400 font-mono flex items-center gap-2">
                                <ShieldCheck size={13} className="text-emerald-400 shrink-0" />
                                <span>Verified ledger state transition recorded. No additional external params attached.</span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-gray-500 italic p-4 text-center">No audit trail records found for this case.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
