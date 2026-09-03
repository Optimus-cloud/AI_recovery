import React, { useState } from 'react';
import { EvaluationResults } from '../types';
import { Play, TrendingUp, Check, X, Sparkles } from 'lucide-react';

interface CampaignRunnerProps {
  onRunCampaign: () => Promise<EvaluationResults | null>;
}

export const CampaignRunner: React.FC<CampaignRunnerProps> = ({ onRunCampaign }) => {
  const [results, setResults] = useState<EvaluationResults | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRun = async () => {
    setIsLoading(true);
    try {
      const res = await onRunCampaign();
      if (res) {
        setResults(res);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  const cleanActionName = (action: string) => {
    return action.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
  };

  return (
    <div className="space-y-6">
      {/* Run Header Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="font-semibold text-white text-lg flex items-center gap-2">
            <Sparkles className="text-violet-400" size={20} />
            <span>Matched Counterfactual Evaluation</span>
          </h3>
          <p className="text-xs text-gray-400 mt-1 max-w-xl">
            Simulate a batch campaign on 100 historical at-risk invoices. Compares World A (Control: generic reminder schedule) against World B (Treatment: RazorResolve AI expected value optimization) under identical latent customer behavior.
          </p>
        </div>

        <button
          onClick={handleRun}
          disabled={isLoading}
          className="bg-violet-600 hover:bg-violet-500 disabled:bg-violet-600/50 text-white font-bold text-sm px-6 py-3 rounded-lg flex items-center justify-center gap-2 transition-all shrink-0 shadow-lg shadow-violet-600/20"
        >
          <Play size={16} />
          {isLoading ? 'Simulating Parallel Worlds...' : 'Run Evaluation Simulation'}
        </button>
      </div>

      {results ? (
        <div className="space-y-6 animate-fade-in">
          {/* Main comparative stat cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Payoff: Incremental Gain */}
            <div className="bg-violet-500/10 border border-violet-500/30 rounded-xl p-5 md:col-span-3 flex flex-col md:flex-row md:items-center justify-between gap-4 relative overflow-hidden">
              <div className="space-y-1">
                <span className="text-xs font-bold text-violet-400 uppercase tracking-wider block">MEASURED INCREMENTAL RECOVERY VS BASELINE</span>
                <h4 className="text-2xl md:text-3xl font-extrabold text-white">
                  +{formatCurrency(results.summary.metrics.incremental_recovered)} Incremental Recovered
                </h4>
                <p className="text-xs text-violet-300">
                  RazorResolve AI strategy outperformed baseline rules by <span className="font-bold text-white">+{results.summary.metrics.improvement_pct.toFixed(1)}%</span> on the exact same 100 cases.
                </p>
              </div>
              <div className="bg-violet-500/20 px-4 py-2.5 rounded-lg border border-violet-500/30 text-center shrink-0">
                <span className="text-[10px] text-violet-300 block uppercase font-semibold">Evaluation Design</span>
                <span className="text-xs text-white font-bold">Simulation-based matched counterfactual evaluation</span>
              </div>
            </div>

            {/* Baseline Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block">World A (Control)</span>
                <h4 className="font-bold text-white mt-0.5">Baseline (Rule-Based)</h4>
              </div>
              
              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Total Recovered</span>
                  <span className="font-bold text-white">{formatCurrency(results.summary.baseline.recovered)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Recovery Rate</span>
                  <span className="font-bold text-gray-300">{results.summary.baseline.recovery_rate}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Interventions sent</span>
                  <span className="font-bold text-gray-300">{results.summary.baseline.interventions}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Recovery / Contact</span>
                  <span className="font-bold text-gray-300">{formatCurrency(results.summary.baseline.roi)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-red-400">Unnecessary outreach</span>
                  <span className="font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded text-xs">{results.summary.baseline.unnecessary_interventions}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-red-400">False recovery drafts</span>
                  <span className="font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded text-xs">{results.summary.baseline.false_recoveries}</span>
                </div>
              </div>
            </div>

            {/* AI Agent Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <div className="border-b border-slate-800 pb-2">
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider block">World B (Treatment)</span>
                <h4 className="font-bold text-white mt-0.5">RazorResolve AI Agent</h4>
              </div>

              <div className="space-y-3 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 font-semibold">Total Recovered</span>
                  <span className="font-bold text-emerald-400 text-base">{formatCurrency(results.summary.ai.recovered)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Recovery Rate</span>
                  <span className="font-bold text-white">{results.summary.ai.recovery_rate}%</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Interventions sent</span>
                  <span className="font-bold text-white">{results.summary.ai.interventions}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Recovery / Contact</span>
                  <span className="font-bold text-white">{formatCurrency(results.summary.ai.roi)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-emerald-400">Unnecessary outreach</span>
                  <span className="font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded text-xs">{results.summary.ai.unnecessary_interventions}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-emerald-400">False recovery drafts</span>
                  <span className="font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded text-xs">{results.summary.ai.false_recoveries}</span>
                </div>
              </div>
            </div>

            {/* Campaign Optimization Summary Ring / Comparison visual */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
              <h4 className="font-semibold text-white border-b border-slate-800 pb-2">Outreach Efficiency</h4>
              
              <div className="space-y-4">
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Recovery Rate (%)</span>
                    <span className="text-white font-semibold">AI: {results.summary.ai.recovery_rate}% vs BL: {results.summary.baseline.recovery_rate}%</span>
                  </div>
                  <div className="h-6 w-full bg-slate-950 rounded-lg overflow-hidden flex flex-col justify-center px-1">
                    <div className="h-2 rounded bg-violet-500 transition-all" style={{ width: `${results.summary.ai.recovery_rate}%` }}></div>
                    <div className="h-1 rounded bg-gray-600 transition-all mt-1" style={{ width: `${results.summary.baseline.recovery_rate}%` }}></div>
                  </div>
                </div>

                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-400">Total Money Recovered (INR)</span>
                  </div>
                  <div className="h-6 w-full bg-slate-950 rounded-lg overflow-hidden flex flex-col justify-center px-1">
                    <div className="h-2 rounded bg-emerald-500 transition-all" style={{ width: '100%' }}></div>
                    <div className="h-1 rounded bg-gray-600 transition-all mt-1" style={{ width: `${(results.summary.baseline.recovered / Math.max(1, results.summary.ai.recovered)) * 100}%` }}></div>
                  </div>
                  <span className="text-[10px] text-gray-500">Green: RazorResolve | Gray: Baseline</span>
                </div>

                <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-[11px] text-gray-400 leading-normal">
                  <span className="font-semibold text-white block">Key AI Optimizations:</span>
                  1. Skips outreach on cases with high natural self-cure rates (Do-Nothing).<br/>
                  2. Audits adjustments before demanding partial payments (0 false drafts).
                </div>
              </div>
            </div>
          </div>

          {/* Table of cases comparing outcomes */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <h4 className="font-semibold text-white">Interactive Trial Cases Breakdown (100 Matched Cases)</h4>
            
            <div className="overflow-x-auto border border-slate-800 rounded-xl max-h-96">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-950 text-xs font-semibold text-gray-400 uppercase border-b border-slate-800">
                    <th className="py-3 px-4">Invoice</th>
                    <th className="py-3 px-4">Customer</th>
                    <th className="py-3 px-4">Issue</th>
                    <th className="py-3 px-4">At Risk</th>
                    <th className="py-3 px-4">Baseline Action / Status</th>
                    <th className="py-3 px-4">RazorResolve Action / Status</th>
                    <th className="py-3 px-4">Incremental Gain</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 text-xs">
                  {results.cases.slice(0, 30).map((c, idx) => {
                    const blSuccess = c.baseline.recovered > 0;
                    const aiSuccess = c.ai.recovered > 0;
                    
                    return (
                      <tr key={idx} className="hover:bg-slate-800/20 transition-colors">
                        <td className="py-3 px-4 font-mono font-semibold text-violet-400">{c.invoice_id}</td>
                        <td className="py-3 px-4">
                          <div>
                            <span className="font-semibold text-white block">{c.customer}</span>
                            <span className="text-[9px] text-gray-400 capitalize">{c.segment.replace('_', ' ')}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-gray-400 capitalize">{c.issue_type.toLowerCase().replace('_', ' ')}</td>
                        <td className="py-3 px-4 text-white font-semibold">{formatCurrency(c.amount_at_risk)}</td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1.5">
                            {blSuccess ? (
                              <Check size={12} className="text-emerald-400" />
                            ) : (
                              <X size={12} className="text-red-400" />
                            )}
                            <span className="text-gray-300">{cleanActionName(c.baseline.action)}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-1.5">
                            {aiSuccess ? (
                              <Check size={12} className="text-emerald-400" />
                            ) : (
                              <X size={12} className="text-red-400" />
                            )}
                            <span className="text-white font-medium">{cleanActionName(c.ai.action)}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 font-bold">
                          {aiSuccess && !blSuccess ? (
                            <span className="text-emerald-400 font-mono">+{formatCurrency(c.amount_at_risk)}</span>
                          ) : (!aiSuccess && blSuccess ? (
                            <span className="text-red-400 font-mono">-{formatCurrency(c.amount_at_risk)}</span>
                          ) : (
                            <span className="text-gray-500 font-mono">--</span>
                          ))}
                        </td>
                      </tr>
                    );
                  })}
                  {results.cases.length > 30 && (
                    <tr className="bg-slate-950/50">
                      <td colSpan={7} className="py-3.5 text-center text-xs font-semibold text-gray-400 italic">
                        Showing top 30 of {results.cases.length} simulated campaign trial cases.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center flex flex-col items-center justify-center space-y-4">
          <TrendingUp className="text-gray-500 bg-slate-950 p-4 rounded-full border border-slate-800" size={64} />
          <div className="space-y-1">
            <h4 className="font-semibold text-white">Simulate Baseline vs AI Agent Outcomes</h4>
            <p className="text-xs text-gray-400 max-w-md mx-auto">
              Ready to verify the Incremental Recovery metric? Clicking the button runs a matched counterfactual simulation on 100 cases under identical customer behavior.
            </p>
          </div>
          <button
            onClick={handleRun}
            disabled={isLoading}
            className="bg-violet-600 hover:bg-violet-500 text-white font-bold text-xs px-6 py-2.5 rounded-lg flex items-center gap-2 transition-all mt-2 shadow-lg shadow-violet-600/20"
          >
            <Play size={12} />
            {isLoading ? 'Running simulation...' : 'Start Evaluation Simulation'}
          </button>
        </div>
      )}
    </div>
  );
};
