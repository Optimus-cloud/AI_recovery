import React, { useState, useEffect } from 'react';
import { AuditLogEntry } from '../types';
import { Terminal, CheckCircle2, ShieldAlert, Clock, RefreshCcw, Layers, Search } from 'lucide-react';

interface ActivityFeedProps {
  logs: AuditLogEntry[];
  onRefresh: () => void;
}

export const ActivityFeed: React.FC<ActivityFeedProps> = ({ logs, onRefresh }) => {
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      onRefresh();
    }, 4000); // Poll feed every 4 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, onRefresh]);

  const formatTime = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toTimeString().split(' ')[0]; // HH:MM:SS
  };

  const getLogIcon = (action: string) => {
    switch (action) {
      case 'SCAN_STARTED':
      case 'SCAN_COMPLETED':
        return <Search className="text-violet-400 shrink-0" size={14} />;
      case 'CASE_OPENED':
        return <Terminal className="text-blue-400 shrink-0" size={14} />;
      case 'RECOVERY_COMPLETED':
        return <CheckCircle2 className="text-emerald-400 shrink-0" size={14} />;
      case 'ACTION_APPROVED':
      case 'CASE_RESOLVED_LEGIT':
        return <CheckCircle2 className="text-purple-400 shrink-0" size={14} />;
      case 'CASE_LEAK_CONFIRMED':
      case 'RECOVERY_FAILED_DECLINED':
        return <ShieldAlert className="text-red-400 shrink-0" size={14} />;
      case 'RECOVERY_FAILED_TIMEOUT':
        return <Clock className="text-gray-400 shrink-0" size={14} />;
      case 'POLICY_UPDATED':
        return <Layers className="text-amber-400 shrink-0" size={14} />;
      default:
        return <Terminal className="text-violet-400 shrink-0" size={14} />;
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Terminal className="text-violet-400" size={18} />
          <div>
            <h3 className="font-semibold text-white">Live Agent Activity Log</h3>
            <p className="text-[10px] text-gray-400 mt-0.5">Real-time trace of autonomous agent execution loop and ledger events</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button 
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`text-[10px] font-bold px-2 py-1 rounded transition-all ${autoRefresh ? 'bg-violet-500/10 text-violet-400 border border-violet-500/20' : 'bg-slate-800 text-gray-500 border border-slate-700'}`}
          >
            {autoRefresh ? 'Auto Live' : 'Paused'}
          </button>
          <button 
            onClick={onRefresh}
            className="bg-slate-950 hover:bg-slate-800 border border-slate-800 text-gray-400 hover:text-white p-1.5 rounded transition-all"
            title="Force refresh"
          >
            <RefreshCcw size={12} />
          </button>
        </div>
      </div>

      <div className="bg-slate-950 border border-slate-800 rounded-lg p-3.5 h-[240px] overflow-y-auto font-mono text-xs space-y-3">
        {logs.length === 0 ? (
          <div className="text-gray-600 text-center py-16 italic">
            Waiting for agent activity... Run a scan or execute an action to begin.
          </div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="flex gap-2.5 items-start animate-fade-in py-1 border-b border-slate-800/30 last:border-0">
              <span className="text-gray-500 select-none shrink-0 font-semibold">{formatTime(log.timestamp)}</span>
              {getLogIcon(log.action)}
              <div className="grow space-y-1">
                <span className="text-violet-400 font-semibold mr-1">[{log.case_id || 'SYSTEM'}]</span>
                <span className="text-gray-300 font-semibold">{log.action.replace('_', ' ')}:</span>
                <span className="text-gray-400 ml-1 leading-relaxed">
                  {log.details.customer ? `Customer ${log.details.customer}` : ''}
                  {log.details.amount ? `, risk amount: ₹${log.details.amount.toLocaleString('en-IN')}` : ''}
                  {log.details.action ? `, action: ${log.details.action}` : ''}
                  {log.details.expected_incremental ? `, expected incremental: ₹${log.details.expected_incremental.toLocaleString('en-IN')}` : ''}
                  {log.details.credit_verified ? `, verified legit credit: ₹${log.details.credit_verified.toLocaleString('en-IN')}` : ''}
                  {log.details.unreconciled_difference ? `, unreconciled underpayment gap: ₹${log.details.unreconciled_difference.toLocaleString('en-IN')}` : ''}
                  {log.details.scope ? `scope: ${log.details.scope}` : ''}
                  {log.details.new_cases_count !== undefined ? `discovered ${log.details.new_cases_count} new risk opportunities` : ''}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
