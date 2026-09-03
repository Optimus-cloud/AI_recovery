# RazorResolve: Official Statistical & Integrity Validation Report

**Author**: Antigravity AI Engineering Team  
**Evaluation Scope**: Official Integrity & Statistical Validation  
**Status**: 100% ISOLATED, EMPIRICALLY VERIFIED & TECHNICALLY DEFENSIBLE  

---

## 1. Evaluation Methodology
RazorResolve uses a **Simulation-Based Matched Counterfactual Evaluation** design:
* **Target Population**: Active at-risk invoices (`OVERDUE`, `FAILED_PAYMENT`, `BROKEN_PROMISE`, `UNDERPAYMENT`).
* **World A (Control)**: Standard Rule-Based Dunning Strategy (naive retry for failed payments, static reminder schedules for overdue payments, blind full-balance demands on underpayments unaware of credits/refunds).
* **World B (Treatment)**: RazorResolve Autonomous AI Agent (evidence-gathering tool invocations, candidate action evaluation, deterministic incremental EV optimization, merchant policy guardrails, and `DO_NOTHING` when natural recovery propensity is high).
* **Isolation Guarantee**: The evaluation module (`evaluation.py`) executes stateless agent decisions (`run_agent_decision_pipeline`) directly and **never reads, mutates, or reuses production `Case` table records**.

---

## 2. Dataset Generation & Composition
* **Synthetic Population**: 1,500 synthetic business customers with latent behavioral ground truth across 5 segments (`reliable`: 65%, `occasional_late`: 18%, `chronic_late`: 9%, `broken_promise`: 5%, `partial_payer`: 3%).
* **Total Ledger Invoices**: 7,773 invoices generated with realistic payment histories and credit notes.
* **Active At-Risk Target Invoices**: 1,002 invoices (~₹5.21 Cr total balance at risk).

---

## 3. Matched Counterfactual Design & Common Latent Scenario
* **Same-Case Verification**: For every evaluated case, `customer_id`, `invoice_id`, `amount_at_risk`, and `issue_type` are 100% identical between Baseline and RazorResolve.
* **Shared Latent Scenario**: Both World A and World B share the **exact same pseudo-random draw** (`latent_roll = eval_rng.random()`).
  * `base_success = (latent_roll <= base_p)`
  * `ai_success = (latent_roll <= ai_p)`
* Randomness is never independently regenerated in a way that artificially favors RazorResolve.

---

## 4. Ground-Truth Isolation & Data Leakage Audit
* **Audited Latent Fields**: `natural_pay_propensity`, `link_responsiveness`, `reminder_responsiveness`, `plan_responsiveness`, `true_promise_reliability`.
* **Verification Result**: **PASSED (0 / 5 fields exposed)**.
* **Information Boundary**: The agent decision engine only observes historical transaction records (kept/broken promise counts, past payment timestamps, invoice due dates, credit adjustments). Latent simulation parameters are never passed to the LLM or agent decision engine.

---

## 5. Reproducibility & Production Scan Contamination Audit
* **Reproducibility Test (Fixed Seed 999, 100 Cases)**:
  * Run 1: Baseline = ₹12,62,888.61 | RazorResolve = ₹33,17,436.66 | Lift = **+₹20,54,548.05**
  * Run 2: Baseline = ₹12,62,888.61 | RazorResolve = ₹33,17,436.66 | Lift = **+₹20,54,548.05**
  * **Result**: 100% Bit-Exact Reproducibility.
* **Contamination Test**:
  * Evaluation Before AI Opportunity Scan: **+₹20,54,548.05**
  * Ran AI Opportunity Scan (1,123 production cases created in database).
  * Evaluation After AI Opportunity Scan: **+₹20,54,548.05**
  * **Result**: 100% Isolated; running the live dashboard does not influence benchmark results.

---

## 6. Multi-Seed Validation Table (Seeds 1 to 10)

Predetermined random seeds evaluated on 100 matched cases:

| Seed | Baseline Recovery | RazorResolve Recovery | Incremental Recovery | Baseline Actions | AI Actions |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | ₹12,98,720.95 | ₹49,33,539.76 | **+₹36,34,818.81** | 100 | 99 |
| **2** | ₹6,96,410.19 | ₹33,73,664.99 | **+₹26,77,254.80** | 100 | 99 |
| **3** | ₹11,96,585.94 | ₹37,76,850.53 | **+₹25,80,264.59** | 100 | 99 |
| **4** | ₹19,66,202.78 | ₹42,56,550.46 | **+₹22,90,347.68** | 100 | 99 |
| **5** | ₹13,99,483.55 | ₹37,12,489.50 | **+₹23,13,005.95** | 100 | 99 |
| **6** | ₹17,18,837.76 | ₹39,99,792.52 | **+₹22,80,954.76** | 100 | 99 |
| **7** | ₹23,30,797.64 | ₹51,51,819.73 | **+₹28,21,022.09** | 100 | 99 |
| **8** | ₹15,68,174.89 | ₹51,92,314.39 | **+₹36,24,139.50** | 100 | 99 |
| **9** | ₹26,43,020.65 | ₹43,33,880.80 | **+₹16,90,860.15** | 100 | 99 |
| **10** | ₹22,33,233.18 | ₹45,06,172.86 | **+₹22,72,939.68** | 100 | 99 |

### Summary Statistics (10 Seeds):
* **Mean Incremental Recovery**: **₹26,18,560.80 (+₹26.19 Lakhs)**
* **Median Incremental Recovery**: **₹24,46,635.27 (+₹24.47 Lakhs)**
* **Minimum Incremental Lift**: **₹16,90,860.15 (+₹16.91 Lakhs)**
* **Maximum Incremental Lift**: **₹36,34,818.81 (+₹36.35 Lakhs)**
* **Standard Deviation ($\sigma$)**: **₹6,13,280.70**
* **Mean AI Interventions**: **99.0** (vs 100.0 Baseline)

---

## 7. Large Batch Scaling Test (100, 500, 1000 Cases)

| Batch Size | Baseline Recovered | RazorResolve Recovered | Incremental Lift | Baseline Rate | AI Rate | AI Actions | Recovery / Action |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **100 Cases** | ₹12,62,888.61 | ₹33,17,436.66 | **+₹20,54,548.05** | 18.8% | 49.4% | 99 | ₹33,509.46 |
| **500 Cases** | ₹74,44,843.81 | ₹1,52,56,576.55 | **+₹78,11,732.74** | 30.1% | 61.6% | 492 | ₹31,009.30 |
| **1,000 Cases** | ₹1,62,91,996.71 | ₹3,55,36,245.39 | **+₹1,92,44,248.68** | 31.3% | 68.2% | 987 | ₹36,004.30 |

---

## 8. Strategy Sanity Comparison (Random vs. Baseline vs. RazorResolve)

| Strategy | Revenue Recovered (100 Cases) | Net Gain vs. Strategy | Behavioral Mechanism |
|---|---|---|---|
| **Rule-Based Baseline** | ₹12,62,888.61 | — (Control) | Naive text reminders fail on chronic non-payers; demands full balance on valid discounts. |
| **Random Strategy** | ₹28,68,153.42 | +₹16,05,264.81 | Randomly dispatches installment plans and links, outperforming passive dunning. |
| **RazorResolve AI** | **₹33,17,436.66** | **+₹20,54,548.05** | Optimizes channel by customer profile, eliminates false underpayment demands, preserves budget with `DO_NOTHING`. |

---

## 9. Outcome-Learning Ablation Study
* **Version A (With Historical Effectiveness Priors)**: ₹33,17,436.66
* **Version B (Without Historical Effectiveness Priors)**: ₹32,83,922.48
* **Marginal Contribution of Bayesian Learning**: **+₹33,514.18**

---

## 10. Controlled Deterministic Sanity Tests
1. **High Natural Payment (95%)**: Agent chooses **`DO_NOTHING`** ($EV_{\text{inc}} = \text{₹0.00}$).
2. **Strong Intervention (₹3L at risk, 25% natural $\rightarrow$ 70% link)**: Payment Link chosen ($EV_{\text{inc}} = \text{+₹1,34,950.00}$).
3. **Legitimate Underpayment (₹1L invoice, ₹80k paid, ₹20k credit)**: Identified as **`NOT_RECOVERABLE`** (0 false collection drafts).
4. **High Value (>₹1L policy gate)**: Intercepted by policy engine as **`PENDING_APPROVAL`**.

---

## 11. Recovery Accounting & Double-Entry Verification
* **Double-Entry Ledger**: Recovered revenue is strictly calculated from `SUM(RecoveryTransaction.amount_recovered)`.
* **Zero Duplication**: Every transaction ID is unique.
* **Separation of Concepts**: `Amount at Risk`, `Expected Incremental Recovery` (theoretical prior), and `Actual Recovered Revenue` (transaction sum) are cleanly segregated.

---

## 12. Simulation Assumptions & Limitations
1. **Simulation Bounds**: Results are measured via **simulation-based matched counterfactual evaluation** on synthetic customer models.
2. **Deterministic Fallback**: In the absence of live LLM API keys, the agent executes via the deterministic decision engine without service disruption.
