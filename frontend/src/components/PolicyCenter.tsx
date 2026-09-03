import React, { useState, useEffect } from 'react';
import { PolicySettings } from '../types';
import { Shield, Save, CheckCircle } from 'lucide-react';

interface PolicyCenterProps {
  policy: PolicySettings;
  onSave: (policy: PolicySettings) => Promise<void>;
}

export const PolicyCenter: React.FC<PolicyCenterProps> = ({ policy, onSave }) => {
  const [autoApprove, setAutoApprove] = useState(policy.auto_approve_threshold);
  const [requireApproval, setRequireApproval] = useState(policy.require_approval_threshold);
  const [maxDiscount, setMaxDiscount] = useState(policy.max_discount_rate * 100);
  const [dailyLimit, setDailyLimit] = useState(policy.daily_limit);
  const [dailyBudget, setDailyBudget] = useState(policy.daily_intervention_budget || 30);
  const [costPenalty, setCostPenalty] = useState(policy.intervention_cost_penalty || 50);
  const [allowedActions, setAllowedActions] = useState<string[]>(policy.allowed_actions);
  const [isSaving, setIsSaving] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  useEffect(() => {
    setAutoApprove(policy.auto_approve_threshold);
    setRequireApproval(policy.require_approval_threshold);
    setMaxDiscount(policy.max_discount_rate * 100);
    setDailyLimit(policy.daily_limit);
    setDailyBudget(policy.daily_intervention_budget || 30);
    setCostPenalty(policy.intervention_cost_penalty || 50);
    setAllowedActions(policy.allowed_actions);
  }, [policy]);

  const actionsList = [
    { key: 'do_nothing', label: 'Do Nothing', desc: 'Allow natural self-cure without outreach fatigue' },
    { key: 'retry_payment', label: 'Payment Retry', desc: 'Automated charge retry on network glitches' },
    { key: 'create_payment_link', label: 'Payment Link', desc: 'Create and send invoice checkout links' },
    { key: 'send_payment_reminder', label: 'Reminder', desc: 'Send soft email/SMS notifications' },
    { key: 'request_payment_commitment', label: 'Promise Request', desc: 'Solicit Promise-to-Pay commitments' },
    { key: 'propose_payment_plan', label: 'Payment Plan', desc: 'Offer 3-month installment schedules' },
    { key: 'investigate_underpayment', label: 'Underpayment Audit', desc: 'Audit ledger adjustments before demanding balance' },
    { key: 'escalate_to_human', label: 'Support Escalation', desc: 'Hand off case to a support operations desk' }
  ];

  const handleActionToggle = (key: string) => {
    if (allowedActions.includes(key)) {
      setAllowedActions(allowedActions.filter(a => a !== key));
    } else {
      setAllowedActions([...allowedActions, key]);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await onSave({
        auto_approve_threshold: Number(autoApprove),
        audit_log_threshold: Number(autoApprove),
        require_approval_threshold: Number(requireApproval),
        allowed_actions: allowedActions,
        max_discount_rate: Number(maxDiscount) / 100,
        daily_limit: Number(dailyLimit),
        daily_intervention_budget: Number(dailyBudget),
        intervention_cost_penalty: Number(costPenalty)
      });
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-6">
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <Shield className="text-violet-400" size={20} />
        <div>
          <h3 className="font-semibold text-white text-lg">Merchant Policy Center</h3>
          <p className="text-xs text-gray-400">Configure safety gates, resource budgets, and action guardrails</p>
        </div>
      </div>

      {showSuccess && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg p-3.5 flex items-center gap-2 text-xs font-semibold">
          <CheckCircle size={16} />
          <span>Policies successfully updated and reloaded by AI Agent!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Threshold sliders / text fields */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-300 block">Auto-Approve Threshold (₹)</label>
            <input
              type="number"
              value={autoApprove}
              onChange={(e) => setAutoApprove(Number(e.target.value))}
              className="w-full bg-slate-950 text-sm text-white px-4 py-2.5 rounded-lg border border-slate-800 focus:outline-none focus:border-violet-500"
            />
            <span className="text-[10px] text-gray-500 block">Actions on cases below this value execute automatically.</span>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-300 block">Require-Approval Threshold (₹)</label>
            <input
              type="number"
              value={requireApproval}
              onChange={(e) => setRequireApproval(Number(e.target.value))}
              className="w-full bg-slate-950 text-sm text-white px-4 py-2.5 rounded-lg border border-slate-800 focus:outline-none focus:border-violet-500"
            />
            <span className="text-[10px] text-gray-500 block">Actions above this value require manual human authorization.</span>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-300 block">Daily Intervention Budget (Cap)</label>
            <input
              type="number"
              value={dailyBudget}
              onChange={(e) => setDailyBudget(Number(e.target.value))}
              className="w-full bg-slate-950 text-sm text-white px-4 py-2.5 rounded-lg border border-slate-800 focus:outline-none focus:border-violet-500"
            />
            <span className="text-[10px] text-gray-500 block">Maximum high-touch interventions allowed per day.</span>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-300 block">Intervention Cost Penalty (₹)</label>
            <input
              type="number"
              value={costPenalty}
              onChange={(e) => setCostPenalty(Number(e.target.value))}
              className="w-full bg-slate-950 text-sm text-white px-4 py-2.5 rounded-lg border border-slate-800 focus:outline-none focus:border-violet-500"
            />
            <span className="text-[10px] text-gray-500 block">Opportunity cost per customer outreach.</span>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-300 block">Max Installment Discount Rate (%)</label>
            <input
              type="number"
              value={maxDiscount}
              onChange={(e) => setMaxDiscount(Number(e.target.value))}
              className="w-full bg-slate-950 text-sm text-white px-4 py-2.5 rounded-lg border border-slate-800 focus:outline-none focus:border-violet-500"
            />
            <span className="text-[10px] text-gray-500 block">Cap on payment plan settlement discounts.</span>
          </div>
        </div>

        {/* Allowed Actions Section */}
        <div className="space-y-3 pt-2">
          <label className="text-xs font-semibold text-gray-300 block">Permitted Autonomous Recovery Tools</label>
          <p className="text-xs text-gray-500">Uncheck an action to disable the agent from autonomously recommending or executing it.</p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
            {actionsList.map((action) => {
              const isChecked = allowedActions.includes(action.key);
              return (
                <div 
                  key={action.key}
                  onClick={() => handleActionToggle(action.key)}
                  className={`p-3.5 rounded-xl border flex items-start gap-3 cursor-pointer transition-all ${isChecked ? 'bg-violet-950/20 border-violet-500/40 text-white' : 'bg-slate-950 border-slate-800 text-gray-400 opacity-60'}`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => {}} 
                    className="mt-1 accent-violet-500 rounded cursor-pointer"
                  />
                  <div>
                    <span className="font-semibold text-sm block">{action.label}</span>
                    <span className="text-xs text-gray-400">{action.desc}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t border-slate-800">
          <button
            type="submit"
            disabled={isSaving}
            className="bg-violet-600 hover:bg-violet-500 disabled:bg-violet-600/50 text-white text-xs font-bold px-6 py-2.5 rounded-lg flex items-center gap-2 transition-all shadow-lg shadow-violet-600/20"
          >
            <Save size={14} />
            {isSaving ? 'Updating Agent Policy...' : 'Save Policy Parameters'}
          </button>
        </div>
      </form>
    </div>
  );
};
