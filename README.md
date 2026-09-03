 RazorResolve — AI Revenue Recovery Agent

> Recover the revenue where intervention actually matters.

RazorResolve is an AI Revenue Recovery Agent built for the Razorpay AI Buildathon — AI Revenue Recovery Track.

Revenue recovery is not just about finding customers who haven't paid. The harder question is:

> Where can an intervention actually change the outcome?

RazorResolve investigates payment and receivables risk, evaluates possible recovery actions, estimates their expected incremental value, prioritizes the best opportunities, operates within merchant-defined policies, and measures the resulting recovery.

The goal is simple:

Don't chase everyone. Make the fewest, smartest interventions that create the most incremental revenue.

---

The Problem

Revenue can slip away for many reasons:

- A payment fails.
- An invoice becomes overdue.
- A customer promises to pay but doesn't.
- A customer pays only part of what is owed.
- A customer may pay naturally without any intervention.

A traditional recovery workflow might look like:

```text
Customer hasn't paid
        ↓
Send reminder / retry payment
        ↓
Wait for payment
```

What if the customer was already going to pay?

In that case, the intervention may add little value while consuming operational effort and potentially creating customer fatigue.

So the real revenue recovery problem is not:

> Who hasn't paid?

It is:

> "Where can our intervention actually make a difference?"

---

## Why RazorResolve Is Different

RazorResolve focuses on incremental recovery, rather than simply the amount outstanding.

```text
Traditional Recovery                      RazorResolve
--------------------                      ------------
Who hasn't paid?                          Revenue at risk
        ↓                                        ↓
Send reminder / retry                     Investigate the situation
        ↓                                        ↓
Hope they pay                             Understand why it happened
                                                 ↓
                                          Evaluate possible actions
                                                 ↓
                                          Estimate expected incremental recovery
                                                 ↓
                                          Prioritize the highest-value opportunities
                                                 ↓
                                          Apply merchant policies
                                                 ↓
                                          Take the action
                                                 ↓
                                          Measure the actual outcome
                                                 ↓
                                          Learn from the result
```

| Traditional Recovery | RazorResolve |
|---|---|
| Focuses on unpaid amounts | Focuses on incremental recovery |
| Identify who hasn't paid | Investigate why revenue is at risk |
| Often uses a default action | Evaluates multiple candidate actions |
| Intervene broadly | Can choose `DO_NOTHING` |
| Action-focused | Action + measurement + feedback |
| Limited context | Uses payment and customer evidence |
| Recovery is the endpoint | Recovery outcomes feed future decisions |

The key idea is:

Revenue recovery shouldn't be about contacting the most customers. It should be about making the fewest, smartest interventions that create the most incremental revenue.

---

 How RazorResolve Works

RazorResolve is one revenue recovery agent equipped with investigation, scoring, policy, execution, and learning tools.

 1. Observe
The agent scans payment and receivables data to identify potential revenue leakage.

 2. Investigate
Instead of treating every unpaid transaction the same, the agent gathers context such as:
- Payment failure history
- Invoice status
- Previous payment behavior
- Promise-to-pay history
- Partial payments
- Refunds and adjustments
- Previous intervention outcomes

 3. Generate Candidate Actions
Depending on the situation, the agent can consider actions such as:
- `DO_NOTHING`
- `RETRY_PAYMENT`
- `CREATE_PAYMENT_LINK`
- `SEND_REMINDER`
- `REQUEST_PAYMENT_COMMITMENT`
- `PROPOSE_PAYMENT_PLAN`
- `INVESTIGATE_UNDERPAYMENT`
- `ESCALATE_TO_HUMAN`

 4. Estimate Outcome
The agent estimates the likelihood of success for different interventions and compares them with the natural payment probability.

 5. Calculate Expected Incremental Recovery
The agent estimates how much additional recovery an intervention could create compared with doing nothing.

 6. Prioritize
When intervention capacity is limited, opportunities are ranked according to expected incremental value. This allows the system to spend recovery effort where it has the highest expected impact.

 7. Apply Merchant Policies
Before execution, the selected action is checked against merchant-defined policies and safety boundaries. High-value, low-confidence, or sensitive situations can require human approval.

 8. Execute
The selected recovery action is executed inside the simulated environment.

 9. Measure
The outcome is recorded in the Recovery Ledger.

 10. Learn
Historical intervention outcomes are used as feedback for future decisions.

---

 # Revenue Recovery Scenarios

RazorResolve currently handles four major revenue leakage situations:

# Failed Payments
Investigates payment failures and determines whether retrying, sending a payment link, reminding the customer, or taking another action is most appropriate.

# Overdue Payments
Prioritizes overdue receivables based on their expected recovery value rather than simply sorting by outstanding amount.

# Broken Promises-to-Pay
Tracks customers who committed to paying and compares their current behavior with their historical promise reliability.

# Underpayments
Investigates payment discrepancies before treating them as recoverable revenue.

The agent can check for:
- Partial payments
- Refunds
- Adjustments
- Credits
- Other transaction context

This prevents the system from blindly chasing amounts that may not actually be recoverable.

---

## Expected Incremental Recovery

The central decision metric in RazorResolve is Expected Incremental Recovery.

Conceptually:

$$\text{Expected Incremental Recovery} = \text{Amount At Risk} \times \left(P(\text{payment with intervention}) - P(\text{payment naturally})\right) - \text{Intervention Cost}$$

The idea is to estimate:

> **How much additional revenue is this intervention expected to create compared with doing nothing?**

For example:
- **Amount at risk**: ₹10,000
- **Probability of natural pay**: 70%
- **Probability after action**: 90%

The intervention may be valuable because it potentially changes the outcome from 70% to 90%.

This is fundamentally different from simply saying:
*"₹10,000 is overdue, so we should contact the customer."*

> [!NOTE]
> Expected incremental recovery is an estimated decision metric. It is not a guarantee of recovery and should not be interpreted as proven causal uplift.

---

## The Value of Doing Nothing

One of the most important decisions an agent can make is sometimes: **`DO_NOTHING`**.

Suppose a customer has a very high probability of paying naturally. Sending another reminder may:
- Add little incremental revenue
- Consume operational capacity
- Increase intervention cost
- Create unnecessary customer contact

RazorResolve can therefore decide that the best intervention is no intervention.

The objective is not **Maximum intervention** — it is **Maximum useful intervention**.

---

## Resource-Aware Recovery

Recovery capacity is not unlimited. A merchant may want to restrict how many interventions the system can perform within a given period.

RazorResolve can use an intervention budget to prioritize opportunities:

```text
Available recovery actions: 30

Opportunity A → Expected incremental recovery: ₹8,500
Opportunity B → Expected incremental recovery: ₹6,900
Opportunity C → Expected incremental recovery: ₹4,200
...
```

The agent focuses the available intervention capacity on the opportunities with the highest expected value. This turns recovery from a simple queue of unpaid customers into an optimal resource allocation problem.

---

## Safety, Policy & Auditability

Revenue recovery should not mean giving an AI unrestricted control over financial workflows.

RazorResolve includes:
- Merchant-defined intervention policies
- Intervention limits and budgets
- Action boundaries
- Human approval for sensitive situations
- High-value / low-confidence safeguards
- Recovery transaction records
- Agent activity logs
- Audit trails

The system separates AI reasoning from financial controls. AI can reason about what to do, while application-level controls determine what the agent is allowed to do.

---

## What Makes RazorResolve Agentic?

RazorResolve is not simply an LLM that generates payment reminders. The agent follows a structured decision loop:

```text
Observe
   ↓
Investigate with tools
   ↓
Build recovery context
   ↓
Evaluate candidate actions
   ↓
Estimate expected incremental value
   ↓
Select action
   ↓
Check policy
   ↓
Execute
   ↓
Record outcome
   ↓
Use feedback for future decisions
```

The system combines:
- Tool-based investigation
- Structured decision-making
- Candidate action evaluation
- Policy enforcement
- Simulated execution
- Transaction-backed recovery measurement
- Historical outcome feedback

The LLM contributes reasoning and action selection, while financial calculations, policy boundaries, and transaction recording remain controlled by deterministic application logic.

---

## Evaluation & Results

### Simulation-Based Matched Counterfactual Evaluation

All financial results reported by RazorResolve are generated using:
- Synthetic customers
- Synthetic transactions
- Simulated intervention outcomes
- Matched counterfactual evaluation

They are not live Razorpay revenue and should not be interpreted as audited banking cash flows.

The baseline and RazorResolve are evaluated on the same cases and underlying latent scenarios, allowing the intervention strategy to be compared fairly.

### 100-Case Benchmark

| Metric | Baseline | RazorResolve |
|---|:---:|:---:|
| **Recovery** | ₹12.63L | ₹33.17L |
| **Recovery Rate** | 18.8% | 49.4% |
| **Incremental Recovery** | — | **+₹20.55L** |

**Result**: RazorResolve recovered an additional ₹20.55L in the 100-case matched simulation.

### Robustness Across 10 Seeds

The benchmark was repeated across 10 different simulation seeds:

| Statistic | Incremental Recovery |
|---|:---:|
| **Mean** | +₹26.24L |
| **Median** | +₹24.47L |
| **Minimum** | +₹16.91L |
| **Maximum** | +₹36.35L |

The results remained positive across all tested seeds.

### 1,000-Case Simulation

At a larger simulation batch:

| Metric | Baseline | RazorResolve |
|---|:---:|:---:|
| **Recovery Rate** | 27.2% | 68.3% |
| **Incremental Recovery** | — | **+₹2.12Cr** |

These results demonstrate how the recovery strategy behaves at a larger simulated scale.

### Recovery Efficiency

Simulated recovery per intervention:

| Metric | Baseline | RazorResolve |
|---|:---:|:---:|
| **Recovery / Action** | ₹14,038 | **₹35,742** |

This reflects the system's ability to prioritize interventions rather than simply maximize the number of interventions.

### Reproducibility

The evaluation framework was designed to avoid relying on a single favorable run. It includes:
- Fixed random seeds
- Matched baseline and AI cases
- Shared latent scenarios
- Hidden ground-truth variables
- Actual simulated recovery outcomes
- Recovery Ledger accounting
- Batch evaluation
- Multi-seed validation
- Automated tests

The financial results are produced by the simulation and can be reproduced using the project code. See [`VALIDATION.md`](./VALIDATION.md) for the detailed validation methodology.

---

## What You Can See in the Demo

The frontend exposes the agent's decision-making rather than only showing a final recovery number:

- **Dashboard**: Shows Recovery KPIs, revenue leakage, recovery performance, and resource/intervention budget.
- **Opportunity Queue**: Shows ranked recovery opportunities, expected incremental value, issue type, recommended action, and `DO_NOTHING` decisions.
- **Case Detail**: Shows investigation context, 10-step decision trace, candidate action matrix, expected values, and selected action.
- **Policy Center**: Shows merchant-defined thresholds, intervention limits, safety controls, and approval boundaries.
- **Campaign Runner**: Shows Baseline vs. RazorResolve matched evaluation results, recovery rates, and incremental recovery.
- **Activity Feed**: Shows agent actions, investigation events, policy decisions, execution events, and audit trail.

---

## Architecture

```text
RazorResolve
│
├── Backend
│   ├── agent.py         ── Agent orchestration and recovery workflow
│   ├── agent_tools.py   ── Investigation, learning, policy and execution tools
│   ├── database.py      ── SQLite session and recovery ledger
│   ├── evaluation.py    ── Matched counterfactual evaluation
│   ├── generator.py     ── Reproducible synthetic data + latent ground truth
│   ├── llm.py           ── LLM reasoning and action selection
│   ├── models.py        ── Database models
│   ├── policy.py        ── Merchant policy and safety controls
│   ├── schemas.py       ── API/data validation schemas
│   └── scoring.py       ── Candidate action scoring and incremental recovery
│
└── Frontend
    ├── Dashboard.tsx    ── Recovery KPIs
    ├── Queue.tsx        ── Value-ranked opportunities
    ├── CaseDetail.tsx   ── Decision trace and candidate actions
    ├── PolicyCenter.tsx ── Merchant safety controls
    ├── CampaignRunner.tsx ── Matched evaluation
    └── ActivityFeed.tsx ── Agent activity and audit trail
```

---

## Project Structure

```text
AI_recovery/
│
├── README.md
├── VALIDATION.md
├── .gitignore
│
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── run.py
│   ├── test_recovery.py
│   │
│   ├── scratch/
│   │   ├── run_official_validation.py
│   │   ├── secret_scan.py
│   │   └── validate_statistically.py
│   │
│   └── app/
│       ├── agent.py
│       ├── agent_tools.py
│       ├── database.py
│       ├── evaluation.py
│       ├── generator.py
│       ├── llm.py
│       ├── main.py
│       ├── models.py
│       ├── policy.py
│       ├── schemas.py
│       └── scoring.py
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── postcss.config.js
    ├── tailwind.config.js
    ├── tsconfig.json
    ├── vite.config.ts
    │
    └── src/
        ├── App.tsx
        ├── index.css
        ├── main.tsx
        ├── types.ts
        │
        └── components/
            ├── ActivityFeed.tsx
            ├── CampaignRunner.tsx
            ├── CaseDetail.tsx
            ├── Dashboard.tsx
            ├── PolicyCenter.tsx
            └── Queue.tsx
```

---

## Run Locally

RazorResolve runs in a self-contained simulated environment.

### Backend

1. Navigate to the backend:
   ```powershell
   cd backend
   ```

2. Create a Python virtual environment:
   ```powershell
   python -m venv venv
   ```

3. Activate virtual environment:
   * **Windows PowerShell**:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   * **Linux / macOS**:
     ```bash
     source venv/bin/activate
     ```

4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

5. *(Optional)* LLM Configuration:
   ```powershell
   cp .env.example .env
   ```
   *Keep real credentials local. Never commit `.env`.*

6. Start the Backend:
   ```powershell
   python run.py
   ```
   *The application creates and seeds the local SQLite simulation database.*
   *Backend API runs on: `http://localhost:8000`*

### Frontend

1. Open a second terminal and navigate to frontend:
   ```powershell
   cd frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Start the development server:
   ```powershell
   npm run dev
   ```
   *Open the application in your browser at `http://localhost:3000`.*

---

## Testing

Run the automated test suite:

```powershell
cd backend
python test_recovery.py
```

The current validation suite contains 8 tests covering core recovery and evaluation behavior.

**Expected result:**
```text
Ran 8 tests in 0.426s ... OK
```

---

## Running the Evaluation

Run the matched counterfactual benchmark:

```powershell
cd backend
python -c "from app.database import SessionLocal; from app.evaluation import run_batch_evaluation; db = SessionLocal(); print(run_batch_evaluation(db, batch_size=100))"
```

The evaluation compares the baseline and RazorResolve using matched simulated cases.

---

## Limitations

RazorResolve is a buildathon prototype, not a production financial recovery system.

The current implementation uses:
- Synthetic customers
- Synthetic transactions
- Simulated payment outcomes
- A local SQLite sandbox
- Simulated intervention execution

The reported financial results are therefore simulation results, not production revenue.

A production implementation would require:
- Real payment and invoice integrations
- Merchant-specific configuration
- Production authentication and authorization
- Compliance controls
- Real communication channels
- Production monitoring
- Human approval workflows
- Production-grade financial infrastructure
- Robust model evaluation on real historical data

The purpose of this project is to demonstrate the agentic decision-making architecture and incremental recovery optimization approach.

---

## Buildathon Context

RazorResolve was built for the:

**Razorpay AI Buildathon — AI Revenue Recovery Track**

The project explores the challenge of finding revenue that is slipping away and determining which intervention is actually worth taking.

The core idea can be summarized in one question:

> **Instead of asking "Who should we chase?", can an AI agent determine "Where can our intervention actually create additional revenue?"**

That's the problem RazorResolve is built to solve.
