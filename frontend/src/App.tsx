import { useState, useEffect, useCallback } from 'react';
import { Dashboard } from './components/Dashboard';
import { Queue } from './components/Queue';
import { CaseDetail } from './components/CaseDetail';
import { PolicyCenter } from './components/PolicyCenter';
import { CampaignRunner } from './components/CampaignRunner';
import { ActivityFeed } from './components/ActivityFeed';
import { Case, DashboardStats, PolicySettings, AuditLogEntry, EvaluationResults } from './types';
import { Shield, LayoutDashboard, Database, ClipboardList, Sliders, PlayCircle, ShieldAlert } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'queue' | 'policy' | 'campaign'>('dashboard');
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);
  
  // Data State
  const [cases, setCases] = useState<Case[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [policy, setPolicy] = useState<PolicySettings | null>(null);
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  
  // UI Status
  const [isScanning, setIsScanning] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);
  const [apiError, setApiError] = useState<string | null>(null);

  // Fetch functions
  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/dashboard`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    }
  }, []);

  const fetchCases = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/opportunities`);
      if (res.ok) {
        const data = await res.json();
        setCases(data);
      }
    } catch (err) {
      console.error("Cases fetch error:", err);
    }
  }, []);

  const fetchPolicy = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/policies`);
      if (res.ok) {
        const data = await res.json();
        setPolicy(data);
      }
    } catch (err) {
      console.error("Policy fetch error:", err);
    }
  }, []);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/activity-feed`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data);
      }
    } catch (err) {
      console.error("Activity feed fetch error:", err);
    }
  }, []);

  // Combined Initializer
  const initializeData = useCallback(async () => {
    setApiError(null);
    try {
      const testRes = await fetch(`${API_BASE}/policies`);
      if (!testRes.ok) {
        await fetch(`${API_BASE}/seed`, { method: 'POST' });
        await fetch(`${API_BASE}/scan`, { method: 'POST' });
      }
      
      await Promise.all([
        fetchDashboard(),
        fetchCases(),
        fetchPolicy(),
        fetchLogs()
      ]);
    } catch (err) {
      console.error("Initialization failed:", err);
      setApiError("Cannot connect to Python FastAPI backend. Ensure uvicorn is running on http://localhost:8000.");
    } finally {
      setIsInitializing(false);
    }
  }, [fetchDashboard, fetchCases, fetchPolicy, fetchLogs]);

  useEffect(() => {
    initializeData();
  }, [initializeData]);

  const handleResetLedger = async () => {
    setIsInitializing(true);
    setApiError(null);
    try {
      const seedRes = await fetch(`${API_BASE}/seed`, { method: 'POST' });
      if (seedRes.ok) {
        await fetch(`${API_BASE}/scan`, { method: 'POST' });
        await Promise.all([
          fetchDashboard(),
          fetchCases(),
          fetchPolicy(),
          fetchLogs()
        ]);
        setSelectedCaseId(null);
      }
    } catch (err) {
      console.error("Failed to reset ledger database:", err);
      setApiError("Failed to reset database. Connection lost.");
    } finally {
      setIsInitializing(false);
    }
  };

  // Scan triggers
  const handleScan = async () => {
    setIsScanning(true);
    try {
      const res = await fetch(`${API_BASE}/scan`, { method: 'POST' });
      if (res.ok) {
        const updatedCases = await res.json();
        setCases(updatedCases);
        await Promise.all([fetchDashboard(), fetchLogs()]);
      }
    } catch (err) {
      console.error("Scan error:", err);
    } finally {
      setIsScanning(false);
    }
  };

  // Execution triggers
  const handleExecuteAction = async (caseId: string, customAction?: string) => {
    try {
      const res = await fetch(`${API_BASE}/cases/${caseId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ custom_action: customAction })
      });
      if (res.ok) {
        const updatedCase = await res.json();
        setCases(prev => prev.map(c => c.id === caseId ? updatedCase : c));
        await Promise.all([fetchDashboard(), fetchLogs()]);
      }
    } catch (err) {
      console.error("Execution error:", err);
    }
  };

  const handleApproveAction = async (caseId: string) => {
    try {
      const res = await fetch(`${API_BASE}/cases/${caseId}/approve`, { method: 'POST' });
      if (res.ok) {
        const updatedCase = await res.json();
        setCases(prev => prev.map(c => c.id === caseId ? updatedCase : c));
        await Promise.all([fetchDashboard(), fetchLogs()]);
      }
    } catch (err) {
      console.error("Approval error:", err);
    }
  };

  const handleSavePolicy = async (policyData: PolicySettings) => {
    try {
      const res = await fetch(`${API_BASE}/policies`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(policyData)
      });
      if (res.ok) {
        const updatedPolicy = await res.json();
        setPolicy(updatedPolicy);
        await fetchLogs();
      }
    } catch (err) {
      console.error("Save policy error:", err);
    }
  };

  const handleRunCampaign = async (): Promise<EvaluationResults | null> => {
    try {
      const res = await fetch(`${API_BASE}/evaluate`, { method: 'POST' });
      if (res.ok) {
        const results = await res.json();
        await Promise.all([fetchDashboard(), fetchCases(), fetchLogs()]);
        return results;
      }
    } catch (err) {
      console.error("Campaign run error:", err);
    }
    return null;
  };

  const selectedCase = cases.find(c => c.id === selectedCaseId);

  return (
    <div className="h-screen bg-slate-950 text-gray-100 flex flex-col font-sans">
      {/* Navbar header */}
      <header className="bg-slate-900 border-b border-slate-800 px-6 py-3.5 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-violet-600/20">
            <Shield className="text-white" size={20} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-bold text-white tracking-tight">RazorResolve</h1>
              <span className="text-[10px] font-semibold uppercase tracking-wider bg-violet-500/10 text-violet-400 border border-violet-500/20 px-2 py-0.5 rounded-full">
                AI Revenue Recovery Agent
              </span>
            </div>
            <p className="text-[11px] text-gray-400 font-medium">
              Recover the revenue where intervention actually matters.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-800/60 border border-slate-700/50 px-3 py-1.5 rounded-lg">
            <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></span>
            <span className="text-xs text-gray-300 font-semibold font-mono">Agent Active</span>
          </div>
        </div>
      </header>

      {/* Main Layout Grid */}
      <div className="grow flex overflow-hidden">
        {/* Navigation Sidebar */}
        <aside className="w-64 bg-slate-900/60 border-r border-slate-800 p-4 flex flex-col gap-2 shrink-0">
          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-wider px-3 mb-2 block">
            Agent Command
          </span>

          <button
            onClick={() => { setActiveTab('dashboard'); setSelectedCaseId(null); }}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'dashboard' && !selectedCaseId ? 'bg-violet-600 text-white shadow-lg shadow-violet-600/20' : 'text-gray-400 hover:text-white hover:bg-slate-800'}`}
          >
            <LayoutDashboard size={18} />
            <span>Dashboard</span>
          </button>

          <button
            onClick={() => { setActiveTab('queue'); setSelectedCaseId(null); }}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'queue' && !selectedCaseId ? 'bg-violet-600 text-white shadow-lg shadow-violet-600/20' : 'text-gray-400 hover:text-white hover:bg-slate-800'}`}
          >
            <ClipboardList size={18} />
            <div className="flex items-center justify-between grow">
              <span>Recovery Queue</span>
              {cases.filter(c => c.status === 'OPEN' || c.status === 'PENDING_APPROVAL').length > 0 && (
                <span className="text-[10px] bg-slate-800 text-gray-300 px-1.5 py-0.5 rounded font-mono">
                  {cases.filter(c => c.status === 'OPEN' || c.status === 'PENDING_APPROVAL').length}
                </span>
              )}
            </div>
          </button>

          <button
            onClick={() => { setActiveTab('policy'); setSelectedCaseId(null); }}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'policy' && !selectedCaseId ? 'bg-violet-600 text-white shadow-lg shadow-violet-600/20' : 'text-gray-400 hover:text-white hover:bg-slate-800'}`}
          >
            <Sliders size={18} />
            <span>Policy Center</span>
          </button>

          <button
            onClick={() => { setActiveTab('campaign'); setSelectedCaseId(null); }}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${activeTab === 'campaign' && !selectedCaseId ? 'bg-violet-600 text-white shadow-lg shadow-violet-600/20' : 'text-gray-400 hover:text-white hover:bg-slate-800'}`}
          >
            <PlayCircle size={18} />
            <span>Campaign Evaluator</span>
          </button>

          {/* Seed trigger */}
          <div className="mt-auto pt-4 border-t border-slate-800">
            <button
              onClick={handleResetLedger}
              className="w-full text-left flex items-center gap-2 text-xs text-gray-500 hover:text-gray-300 font-mono py-2 px-3 hover:bg-slate-800/40 rounded-md transition-colors"
            >
              <Database size={12} />
              <span>Reset & Seed Ledger</span>
            </button>
          </div>
        </aside>

        {/* Central Content Area */}
        <main className="grow p-6 overflow-y-auto space-y-6">
          {apiError ? (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl p-5 flex gap-3.5 items-start">
              <ShieldAlert size={20} className="shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-white">Connection Error</h4>
                <p className="text-xs text-red-300 mt-1 leading-normal">{apiError}</p>
                <button
                  onClick={initializeData}
                  className="bg-red-500 text-slate-950 text-xs font-bold px-4 py-2 rounded-lg mt-3 transition-all hover:bg-red-400"
                >
                  Retry Connection
                </button>
              </div>
            </div>
          ) : isInitializing ? (
            <div className="flex flex-col items-center justify-center h-full space-y-3">
              <span className="w-8 h-8 border-4 border-violet-600 border-t-transparent rounded-full animate-spin"></span>
              <span className="text-sm text-gray-400 font-medium">Booting Agentic Ledger Sandbox...</span>
            </div>
          ) : selectedCase ? (
            <CaseDetail
              caseData={selectedCase}
              onBack={() => setSelectedCaseId(null)}
              onExecute={handleExecuteAction}
              onApprove={handleApproveAction}
            />
          ) : (
            <>
              {activeTab === 'dashboard' && stats && (
                <Dashboard 
                  stats={stats} 
                  onNavigateToQueue={() => setActiveTab('queue')} 
                />
              )}
              {activeTab === 'queue' && (
                <Queue
                  cases={cases}
                  onSelectCase={(id) => setSelectedCaseId(id)}
                  onScan={handleScan}
                  isScanning={isScanning}
                />
              )}
              {activeTab === 'policy' && policy && (
                <PolicyCenter
                  policy={policy}
                  onSave={handleSavePolicy}
                />
              )}
              {activeTab === 'campaign' && (
                <CampaignRunner
                  onRunCampaign={handleRunCampaign}
                />
              )}
              
              {/* Bottom activity log tray */}
              <ActivityFeed 
                logs={logs} 
                onRefresh={fetchLogs} 
              />
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
