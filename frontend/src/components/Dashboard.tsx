import React from 'react';
import { DashboardStats } from '../types';
import { AlertCircle, ArrowUpRight, CheckCircle2, ShieldAlert, TrendingUp, Wallet, Zap, FileText, Activity, Layers } from 'lucide-react';

interface DashboardProps {
  stats: DashboardStats;
  onNavigateToQueue: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ stats, onNavigateToQueue }) => {
  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  const categories = [
    { name: 'Failed Payments', key: 'FAILED_PAYMENT', color: '#3B82F6', icon: Zap },
    { name: 'Overdue Invoices', key: 'OVERDUE_PAYMENT', color: '#F59E0B', icon: FileText },
    { name: 'Broken Promises', key: 'BROKEN_PROMISE', color: '#EF4444', icon: ShieldAlert },
    { name: 'Underpayments', key: 'UNDERPAYMENT', color: '#10B981', icon: AlertCircle }
  ];

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        
        {/* Card 1: Revenue at Risk */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
          <div className="absolute right-4 top-4 text-red-400 bg-red-500/10 p-2 rounded-lg">
            <ShieldAlert size={20} />
          </div>
          <p className="text-sm font-medium text-gray-400">Total Revenue At Risk</p>
          <p className="text-2xl font-bold mt-2 text-white">{formatCurrency(stats.total_at_risk)}</p>
          <div className="flex items-center gap-1 mt-3 text-xs text-red-400">
            <span>Outstanding active leaks</span>
          </div>
        </div>

        {/* Card 2: Revenue Recovered (Real Ledger) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
          <div className="absolute right-4 top-4 text-emerald-400 bg-emerald-500/10 p-2 rounded-lg">
            <CheckCircle2 size={20} />
          </div>
          <p className="text-sm font-medium text-gray-400">Total Revenue Recovered</p>
          <p className="text-2xl font-bold mt-2 text-emerald-400">{formatCurrency(stats.revenue_recovered)}</p>
          <div className="flex items-center gap-1 mt-3 text-xs text-emerald-400">
            <ArrowUpRight size={14} />
            <span>Verified double-entry ledger</span>
          </div>
        </div>

        {/* Card 3: Recoverable & Incremental */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
          <div className="absolute right-4 top-4 text-violet-400 bg-violet-500/10 p-2 rounded-lg">
            <TrendingUp size={20} />
          </div>
          <p className="text-sm font-medium text-gray-400">Est. Incremental Recovery</p>
          <p className="text-2xl font-bold mt-2 text-violet-400">{formatCurrency(stats.estimated_incremental)}</p>
          <div className="flex items-center gap-1 mt-3 text-xs text-violet-300">
            <span>Expected lift vs Do-Nothing</span>
          </div>
        </div>

        {/* Card 4: Recovery Rate */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 relative overflow-hidden">
          <div className="absolute right-4 top-4 text-emerald-400 bg-emerald-500/10 p-2 rounded-lg">
            <Wallet size={20} />
          </div>
          <p className="text-sm font-medium text-gray-400">Recovery Rate</p>
          <p className="text-2xl font-bold mt-2 text-white">{stats.recovery_rate.toFixed(1)}%</p>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-4 overflow-hidden">
            <div 
              className="bg-emerald-500 h-full transition-all duration-500" 
              style={{ width: `${Math.min(100, stats.recovery_rate)}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Main Dashboard Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Breakdown of opportunities */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center pb-2 border-b border-slate-800">
            <h3 className="font-semibold text-white">Revenue Leak Type Breakdown</h3>
            <button 
              onClick={onNavigateToQueue} 
              className="text-xs font-semibold text-violet-400 hover:text-violet-300 flex items-center gap-1"
            >
              View Queue <ArrowUpRight size={14} />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
            {categories.map((cat) => {
              const value = stats.breakdown[cat.key as keyof typeof stats.breakdown] || 0;
              const percent = stats.total_at_risk > 0 ? (value / stats.total_at_risk * 100) : 0;
              const CatIcon = cat.icon;

              return (
                <div key={cat.key} className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-md" style={{ backgroundColor: `${cat.color}20`, color: cat.color }}>
                        <CatIcon size={16} />
                      </div>
                      <span className="text-sm font-medium text-gray-300">{cat.name}</span>
                    </div>
                    <span className="text-xs font-bold text-gray-400">{percent.toFixed(0)}%</span>
                  </div>
                  <div>
                    <span className="text-lg font-bold text-white">{formatCurrency(value)}</span>
                  </div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="h-full rounded-full" 
                      style={{ width: `${percent}%`, backgroundColor: cat.color }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Quick Informational Notice */}
          <div className="bg-violet-500/5 border border-violet-500/20 rounded-xl p-4 mt-2 flex gap-3">
            <Zap className="text-violet-400 shrink-0 mt-0.5" size={18} />
            <div className="text-xs text-violet-300 leading-relaxed">
              <span className="font-semibold">Counterfactual Optimization Model:</span> RazorResolve evaluates candidate recovery actions against natural self-payment baselines (<code className="bg-slate-950 px-1 py-0.5 rounded text-violet-200">P_action - P_natural</code>). If expected incremental lift is negligible, the agent selects <span className="font-semibold text-white">Do Nothing</span> to eliminate customer fatigue and save operational bandwidth.
            </div>
          </div>
        </div>

        {/* Right side KPIs */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
          <h3 className="font-semibold text-white pb-2 border-b border-slate-800">Resource & Learning KPIs</h3>
          
          <div className="space-y-3">
            {/* Daily Intervention Budget */}
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400 flex items-center gap-1.5">
                  <Layers size={14} className="text-violet-400" />
                  Daily Intervention Budget
                </span>
                <span className="font-mono font-bold text-white">
                  {stats.daily_budget_remaining} / {stats.daily_budget_total} Available
                </span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div 
                  className="bg-violet-500 h-full transition-all duration-500" 
                  style={{ width: `${Math.min(100, (stats.daily_budget_remaining / max(1, stats.daily_budget_total)) * 100)}%` }}
                ></div>
              </div>
            </div>

            {/* Learned Action Success Rate */}
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Activity size={16} className="text-emerald-400" />
                <span className="text-xs text-gray-300">Empirical Action Success</span>
              </div>
              <span className="font-mono font-bold text-emerald-400 text-xs bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                {(stats.learned_success_rate * 100).toFixed(1)}%
              </span>
            </div>

            {/* High/Critical Priority */}
            <div className="flex justify-between items-center bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-gray-400">High/Critical Priority</span>
              <span className="font-bold text-red-400 bg-red-500/10 px-2 py-0.5 rounded text-xs">
                {stats.high_priority_count} Cases
              </span>
            </div>

            {/* Actions Executed */}
            <div className="flex justify-between items-center bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-gray-400">Ledger Executions</span>
              <span className="font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded text-xs">
                {stats.actions_executed_count} Transactions
              </span>
            </div>

            {/* Human Escalations */}
            <div className="flex justify-between items-center bg-slate-950 p-3 rounded-lg border border-slate-800">
              <span className="text-xs text-gray-400">Escalated to Human</span>
              <span className="font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded text-xs">
                {stats.human_escalations} Cases
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

function max(a: number, b: number) {
  return a > b ? a : b;
}
