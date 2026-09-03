 RazorResolve - Autonomous AI Revenue Recovery Agent

> "Recover the revenue where intervention actually matters."
> 
> RazorResolve is an autonomous AI Revenue Recovery Agent that investigates payment and receivables risk, selects the highest-value recovery intervention, acts within merchant policies, and measures incremental recovery.

Designed for the Razorpay Buildathon AI Revenue Recovery Track.

---

 Quick Start Instructions

This project runs in a self-contained simulated sandbox. Follow these commands to launch the backend and frontend in Windows, Linux, or macOS.

 1. Setup & Start Backend

Navigate to the `backend/` directory, set up a Python virtual environment, install requirements, and run the server.

```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# or
source venv/bin/activate      # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# (Optional) Setup environment variables if using live LLMs
cp .env.example .env

# Run initialization and launch server (auto-creates and seeds SQLite database)
python run.py
```

The backend starts a SQLite database sandbox and triggers an autonomous agent opportunity scan. The API will be available on `http://localhost:8000`.

 2. Setup & Start Frontend

Navigate to the `frontend/` directory, install node modules, and start the Vite React development server.

```powershell
# Navigate to frontend in a new terminal window
cd frontend

# Install packages
npm install

# Run the development server
npm run dev
```

Open your browser to `http://localhost:3000` to view the command dashboard!

---

 System Architecture & Key Modules

```
├── backend/
│   ├── app/
│   │   ├── agent.py         # Autonomous opportunity scanner, investigation loop, and action executor
│   │   ├── agent_tools.py   # Explicit callable tools (investigation, learning, policy, execution)
│   │   ├── database.py      # SQLite session and engine setup
│   │   ├── evaluation.py    # Matched counterfactual evaluation engine & Monte Carlo simulator
│   │   ├── generator.py     # Reproducible synthetic data generation with latent ground truth
│   │   ├── llm.py           # LLM client & deterministic reasoning action selector
│   │   ├── models.py        # SQLAlchemy models (RecoveryTransaction, Customer, Invoice, etc.)
│   │   ├── policy.py        # Merchant policy engine & safety guardrails
│   │   ├── schemas.py       # Pydantic validation schemas
│   │   └── scoring.py       # Candidate actions evaluation matrix & counterfactual math
│   ├── requirements.txt     # Python packages
│   ├── test_recovery.py     # Automated unit & validation test suite (TEST A - TEST H)
│   └── run.py               # Database migrator & startup script
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Dashboard.tsx       # Real ledger KPIs, resource budget bar, leak breakdown
    │   │   ├── Queue.tsx           # Value-ranked opportunity queue with DO_NOTHING badges
    │   │   ├── CaseDetail.tsx      # Multi-step Decision Trace & Candidate Actions Matrix
    │   │   ├── PolicyCenter.tsx    # Safety thresholds, daily budget cap, cost penalty
    │   │   ├── CampaignRunner.tsx  # Matched counterfactual evaluation comparison
    │   │   └── ActivityFeed.tsx    # Live real-time agent audit log tray
    │   ├── App.tsx          # Main state orchestrator
    │   ├── types.ts         # TypeScript interfaces
    │   └── main.tsx         # App bootstrap entry
    ├── package.json         # Node dependencies
    └── vite.config.ts       # Vite proxy configuration
```

---

 Core Mathematical & Agentic Framework

1. Counterfactual Incremental Recovery ($EV_{\text{incremental}}$)
The agent estimates the net lift of an intervention over the natural self-cure baseline:
$$EV_{\text{incremental}} = \max\left(0, \text{Amount At Risk} \times (P_{\text{action}} - P_{\text{natural}}) - \text{Intervention Cost}\right)$$

 2. Candidate Actions Evaluation Matrix & DO_NOTHING
For every identified risk, the agent evaluates all relevant candidates (`DO_NOTHING`, `RETRY_PAYMENT`, `CREATE_PAYMENT_LINK`, `SEND_REMINDER`, `REQUEST_PAYMENT_COMMITMENT`, `PROPOSE_PAYMENT_PLAN`, `INVESTIGATE_UNDERPAYMENT`, `ESCALATE_TO_HUMAN`).
* If $P_{\text{natural}} \ge 0.90$ (e.g. reliable corporate client), the agent selects **`DO_NOTHING`** to save operational budget and prevent customer fatigue.

 3. Real Double-Entry Recovery Ledger
Total revenue recovered is computed strictly from verified transaction logs:
$$\text{TOTAL REVENUE RECOVERED} = \sum_{\text{outcome} = \text{'SUCCESS'}} \text{amount\_recovered from RecoveryTransaction}$$

 4. Bayesian Outcome Learning
Historical feedback records (`intervention_feedback`) continuously update action effectiveness:
$$\text{Posterior Rate} = \frac{\text{Prior Successes} + \text{Observed Successes}}{\text{Prior Total} + \text{Observed Trials}}$$

---

 Testing & Evaluation

 Run Automated Test Suite
```powershell
cd backend
python test_recovery.py
```
Outputs: `Ran 8 tests in 0.735s ... OK`

 Run Matched Counterfactual Benchmark
```powershell
cd backend
python -c "from app.database import SessionLocal; from app.evaluation import run_batch_evaluation; db = SessionLocal(); print(run_batch_evaluation(db, batch_size=100))"
```

---

 Simulation Disclaimer
All evaluation benchmarks and financial lifts reported in this repository are derived from **simulation-based matched counterfactual evaluation** on synthetic customer models. They reflect mathematical simulation outcomes rather than audited live banking cash flows.
