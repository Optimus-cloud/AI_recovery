import React, { useState, useMemo } from 'react';
import { Case } from '../types';
import { Search, Filter, ArrowUpDown, ChevronRight, Eye, RefreshCw } from 'lucide-react';

interface QueueProps {
  cases: Case[];
  onSelectCase: (caseId: string) => void;
  onScan: () => void;
  isScanning: boolean;
}

type SortField = 'amount_at_risk' | 'expected_incremental_recovery' | 'p_intervene' | 'priority' | 'status';
type SortOrder = 'asc' | 'desc';

export const Queue: React.FC<QueueProps> = ({ cases, onSelectCase, onScan, isScanning }) => {
  const [search, setSearch] = useState('');
  const [issueTypeFilter, setIssueTypeFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortField, setSortField] = useState<SortField>('expected_incremental_recovery');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  // Status mapping colors
  const statusColors: Record<string, string> = {
    OPEN: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    PENDING_APPROVAL: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    EXECUTED: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
    RECOVERED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    ESCALATED: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    FAILED: 'bg-red-500/10 text-red-400 border-red-500/20',
    IGNORED: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
    DO_NOTHING: 'bg-slate-700/20 text-slate-400 border-slate-700/30'
  };

  // Priority mapping colors
  const priorityColors: Record<string, string> = {
    LOW: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
    MEDIUM: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    HIGH: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    CRITICAL: 'bg-red-500/10 text-red-400 border-red-500/20',
  };

  const priorityOrder = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };

  const filteredAndSortedCases = useMemo(() => {
    return cases
      .filter((c) => {
        const customerName = c.customer_name || '';
        const caseId = c.id || '';
        const matchesSearch = customerName.toLowerCase().includes((search || '').toLowerCase()) || caseId.toLowerCase().includes((search || '').toLowerCase());
        
        const matchesType = issueTypeFilter === 'ALL' || c.issue_type === issueTypeFilter;
        const matchesPriority = priorityFilter === 'ALL' || c.priority === priorityFilter;
        
        let matchesStatus = false;
        if (statusFilter === 'ALL') {
          matchesStatus = true;
        } else if (statusFilter === 'PENDING_APPROVAL') {
          matchesStatus = c.status === 'PENDING_APPROVAL' || (c.status === 'OPEN' && c.human_approval_required === true);
        } else if (statusFilter === 'OPEN') {
          matchesStatus = c.status === 'OPEN' && c.human_approval_required === false;
        } else {
          matchesStatus = c.status === statusFilter;
        }
        
        return matchesSearch && matchesType && matchesPriority && matchesStatus;
      })
      .sort((a, b) => {
        let valA: any = a[sortField];
        let valB: any = b[sortField];

        if (sortField === 'priority') {
          valA = priorityOrder[a.priority] || 0;
          valB = priorityOrder[b.priority] || 0;
        }

        if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
        if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
        return 0;
      });
  }, [cases, search, issueTypeFilter, priorityFilter, statusFilter, sortField, sortOrder]);

  const cleanActionName = (action: string) => {
    return action.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
  };

  const cleanIssueName = (issue: string) => {
    return issue.replace('_', ' ');
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
      {/* Table Actions Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h3 className="font-semibold text-white text-lg">Revenue Recovery Queue</h3>
          <p className="text-xs text-gray-400 mt-1">
            Prioritized strictly by Expected Incremental Recovery: Amount × (P_action - P_natural)
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onScan}
            disabled={isScanning}
            className="bg-violet-600 hover:bg-violet-500 disabled:bg-violet-600/50 text-white text-xs font-semibold px-4 py-2.5 rounded-lg flex items-center gap-2 transition-all shadow-lg shadow-violet-600/20"
          >
            <RefreshCw size={14} className={isScanning ? 'animate-spin' : ''} />
            {isScanning ? 'Autonomous Agent Scanning...' : 'Run AI Recovery Scan'}
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {/* Search */}
        <div className="relative">
          <Search size={16} className="absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            placeholder="Search customer or case ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 text-sm text-gray-200 pl-10 pr-4 py-2.5 rounded-lg border border-slate-800 focus:outline-none focus:border-violet-500"
          />
        </div>

        {/* Issue Type */}
        <div className="flex items-center bg-slate-950 rounded-lg border border-slate-800 px-3 py-1">
          <Filter size={14} className="text-gray-400 mr-2" />
          <select
            value={issueTypeFilter}
            onChange={(e) => setIssueTypeFilter(e.target.value)}
            className="w-full bg-transparent text-sm text-gray-300 py-1.5 focus:outline-none"
          >
            <option value="ALL">All Issues</option>
            <option value="FAILED_PAYMENT">Failed Payments</option>
            <option value="OVERDUE_PAYMENT">Overdue Payments</option>
            <option value="BROKEN_PROMISE">Broken Promises</option>
            <option value="UNDERPAYMENT">Underpayments</option>
          </select>
        </div>

        {/* Priority Filter */}
        <div className="flex items-center bg-slate-950 rounded-lg border border-slate-800 px-3 py-1">
          <Filter size={14} className="text-gray-400 mr-2" />
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="w-full bg-transparent text-sm text-gray-300 py-1.5 focus:outline-none"
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        {/* Status Filter */}
        <div className="flex items-center bg-slate-950 rounded-lg border border-slate-800 px-3 py-1">
          <Filter size={14} className="text-gray-400 mr-2" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full bg-transparent text-sm text-gray-300 py-1.5 focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open (Ready)</option>
            <option value="PENDING_APPROVAL">Pending Approval</option>
            <option value="DO_NOTHING">Do Nothing (Self-Recovering)</option>
            <option value="ESCALATED">Escalated</option>
            <option value="RECOVERED">Recovered</option>
            <option value="FAILED">Failed</option>
            <option value="IGNORED">Legitimate Adjustments</option>
          </select>
        </div>
      </div>

      {/* Table Data */}
      <div className="overflow-x-auto border border-slate-800 rounded-xl">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-950 text-xs font-semibold text-gray-400 uppercase border-b border-slate-800">
              <th className="py-4 px-4">Case ID</th>
              <th className="py-4 px-4 cursor-pointer hover:text-white" onClick={() => handleSort('priority')}>
                <div className="flex items-center gap-1">Priority <ArrowUpDown size={12} /></div>
              </th>
              <th className="py-4 px-4">Customer</th>
              <th className="py-4 px-4">Issue</th>
              <th className="py-4 px-4 cursor-pointer hover:text-white" onClick={() => handleSort('amount_at_risk')}>
                <div className="flex items-center gap-1">At Risk <ArrowUpDown size={12} /></div>
              </th>
              <th className="py-4 px-4 cursor-pointer hover:text-white" onClick={() => handleSort('p_intervene')}>
                <div className="flex items-center gap-1">P (Nat → Int) <ArrowUpDown size={12} /></div>
              </th>
              <th className="py-4 px-4 cursor-pointer hover:text-white text-right" onClick={() => handleSort('expected_incremental_recovery')}>
                <div className="flex items-center justify-end gap-1">Expected Recovery <ArrowUpDown size={12} /></div>
              </th>
              <th className="py-4 px-4">Selected Action</th>
              <th className="py-4 px-4 cursor-pointer" onClick={() => handleSort('status')}>
                <div className="flex items-center gap-1">Status <ArrowUpDown size={12} /></div>
              </th>
              <th className="py-4 px-4"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-sm">
            {filteredAndSortedCases.length === 0 ? (
              <tr>
                <td colSpan={10} className="py-12 text-center text-gray-500 text-sm">
                  {isScanning ? 'Agent is actively scanning and evaluating cases...' : 'No opportunities found. Run a ledger scan to detect leaks.'}
                </td>
              </tr>
            ) : (
              filteredAndSortedCases.map((c) => (
                <tr key={c.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3.5 px-4 font-mono text-xs text-violet-400 font-semibold">{c.id}</td>
                  <td className="py-3.5 px-4">
                    <span className={`inline-flex items-center border rounded-full px-2 py-0.5 text-xs font-bold ${priorityColors[c.priority] || 'bg-gray-500/10'}`}>
                      {c.priority}
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <div>
                      <span className="font-semibold text-white block">{c.customer_name}</span>
                      <span className="text-[10px] text-gray-400 capitalize bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 inline-block mt-0.5">
                        {c.customer_segment.replace('_', ' ')}
                      </span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-xs font-medium text-gray-300 capitalize">
                    {cleanIssueName(c.issue_type).toLowerCase()}
                  </td>
                  <td className="py-3.5 px-4 font-semibold text-white">
                    {formatCurrency(c.amount_at_risk)}
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1">
                      <span className="text-gray-400 font-mono text-xs">{(c.p_natural * 100).toFixed(0)}%</span>
                      <ChevronRight size={10} className="text-gray-500" />
                      <span className="text-emerald-400 font-bold font-mono text-xs">{(c.p_intervene * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-right font-bold font-mono text-violet-400">
                    {formatCurrency(c.expected_incremental_recovery)}
                  </td>
                  <td className="py-3.5 px-4 text-xs font-medium text-gray-300">
                    <div className="flex items-center gap-1.5">
                      <span>{cleanActionName(c.recommended_action)}</span>
                      {c.budget_allocated === false && (
                        <span className="text-[9px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20 px-1 rounded">
                          Budget Cap
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <span className={`inline-flex items-center border rounded-full px-2 py-0.5 text-[10px] font-bold tracking-wider ${statusColors[c.status] || 'bg-gray-500/10'}`}>
                      {c.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-right">
                    <button
                      onClick={() => onSelectCase(c.id)}
                      className="bg-slate-950 hover:bg-violet-950 border border-slate-800 hover:border-violet-800 text-gray-300 hover:text-white p-2 rounded-lg transition-all"
                      title="Inspect Opportunity & Decision Trace"
                    >
                      <Eye size={14} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
