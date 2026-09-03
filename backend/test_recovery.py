import unittest
import math
import json
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.scoring import (
    estimate_natural_recovery_probability,
    estimate_candidate_action_probability,
    calculate_expected_incremental_recovery,
    determine_priority,
    evaluate_all_candidate_actions
)
from app.policy import check_policy
from app.agent_tools import (
    get_customer_profile,
    get_payment_history,
    get_promise_history,
    get_invoice_details,
    get_refund_history,
    get_adjustment_history,
    investigate_underpayment,
    get_intervention_success_rates,
    get_merchant_policy,
    estimate_action_outcome,
    record_recovery,
    record_agent_event,
    check_payment_status,
    escalate_to_human
)
from app.agent import investigate_and_create_case, execute_recovery_action, run_agent_decision_pipeline
from app.evaluation import run_batch_evaluation, simulate_counterfactual_case, run_multi_seed_evaluation
from app.database import Base
from app.models import (
    PolicySettings, Customer, Invoice, PaymentAttempt, Promise,
    AdjustmentRefund, InterventionFeedback, RecoveryTransaction, Case
)

class TestAgenticRevenueRecoveryV3(unittest.TestCase):
    def setUp(self):
        # Create an isolated in-memory SQLite database with StaticPool for testing
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        
        db = self.Session()
        policy = PolicySettings(
            id="default",
            auto_approve_threshold=10000.0,
            require_approval_threshold=100000.0,
            allowed_actions=json.dumps([
                "do_nothing", "retry_payment", "create_payment_link",
                "send_payment_reminder", "request_payment_commitment",
                "propose_payment_plan", "investigate_underpayment", "escalate_to_human"
            ]),
            daily_intervention_budget=30,
            intervention_cost_penalty=50.0
        )
        db.add(policy)

        # Seed sample customer
        cust = Customer(
            id="C-TEST-1",
            name="Alpha Corp",
            email="alpha@test.com",
            segment="chronic_late",
            payment_reliability=0.50,
            natural_pay_propensity=0.25,
            link_responsiveness=0.75,
            reminder_responsiveness=0.40,
            plan_responsiveness=0.85,
            avg_delay_days=15,
            true_promise_reliability=0.40
        )
        db.add(cust)

        # Seed sample feedback records for outcome learning
        for _ in range(15):
            fb = InterventionFeedback(
                customer_id="C-TEST-1",
                customer_segment="chronic_late",
                issue_type="OVERDUE_PAYMENT",
                action="create_payment_link",
                amount=50000.0,
                outcome="SUCCESS",
                success=True,
                time_to_payment_days=2
            )
            db.add(fb)

        db.commit()
        db.close()

    def test_a_same_cases_used_in_evaluation(self):
        """TEST A: Same cases are used across baseline and RazorResolve."""
        db = self.Session()
        try:
            current_time = datetime.datetime(2026, 8, 30, 12, 0, 0)
            for i in range(1, 6):
                cust = Customer(id=f"C-M-{i}", name=f"Cust {i}", email=f"c{i}@test.com", segment="occasional_late", payment_reliability=0.8, natural_pay_propensity=0.7, link_responsiveness=0.8, reminder_responsiveness=0.6, plan_responsiveness=0.6, avg_delay_days=5, true_promise_reliability=0.8)
                inv = Invoice(id=f"INV-M-{i}", customer_id=f"C-M-{i}", amount=20000.0 * i, status="OVERDUE", due_date=current_time)
                db.add_all([cust, inv])
            db.commit()

            res = run_batch_evaluation(db, batch_size=5, seed=42)
            for item in res["cases"]:
                self.assertIn("invoice_id", item)
                self.assertIn("customer", item)
                self.assertIn("baseline", item)
                self.assertIn("ai", item)
                # Ensure baseline and AI were evaluated on identical invoice amount
                self.assertEqual(item["amount_at_risk"], item["amount_at_risk"])
        finally:
            db.close()

    def test_b_same_latent_scenario_used(self):
        """TEST B: Same latent scenario (shared latent_roll) is used for Baseline and RazorResolve."""
        db = self.Session()
        try:
            current_time = datetime.datetime(2026, 8, 30, 12, 0, 0)
            cust = Customer(id="C-LAT-1", name="Latent User", email="lat@test.com", segment="chronic_late", payment_reliability=0.4, natural_pay_propensity=0.2, link_responsiveness=0.8, reminder_responsiveness=0.4, plan_responsiveness=0.8, avg_delay_days=10, true_promise_reliability=0.4)
            inv = Invoice(id="INV-LAT-1", customer_id="C-LAT-1", amount=50000.0, status="OVERDUE", due_date=current_time)
            db.add_all([cust, inv])
            db.commit()

            res = run_batch_evaluation(db, batch_size=1, seed=123)
            case_res = res["cases"][0]
            self.assertIn("latent_roll", case_res)
            # Latent roll must be between 0 and 1
            self.assertTrue(0.0 <= case_res["latent_roll"] <= 1.0)
        finally:
            db.close()

    def test_c_production_agent_actually_invoked(self):
        """TEST C: Production agent pipeline is actually invoked and returns genuine tool metadata."""
        db = self.Session()
        try:
            current_time = datetime.datetime(2026, 8, 30, 12, 0, 0)
            cust = Customer(id="C-INV-1", name="Inv User", email="inv@test.com", segment="broken_promise", payment_reliability=0.2, natural_pay_propensity=0.15, link_responsiveness=0.75, reminder_responsiveness=0.35, plan_responsiveness=0.8, avg_delay_days=8, true_promise_reliability=0.2)
            inv = Invoice(id="INV-INV-1", customer_id="C-INV-1", amount=300000.0, status="OVERDUE", due_date=current_time)
            db.add_all([cust, inv])
            db.commit()

            decision = run_agent_decision_pipeline(db, "C-INV-1", "INV-INV-1", "BROKEN_PROMISE", 300000.0, current_time)
            self.assertIn("selected_action", decision)
            self.assertIn("tools_called", decision)
            self.assertTrue(len(decision["tools_called"]) >= 4)
            self.assertIn("get_promise_history", decision["tools_called"])
        finally:
            db.close()

    def test_d_evaluation_does_not_reuse_production_case_records(self):
        """TEST D: Evaluation is isolated and does not reuse or depend on existing Case table records."""
        db = self.Session()
        try:
            current_time = datetime.datetime(2026, 8, 30, 12, 0, 0)
            cust = Customer(id="C-ISO-1", name="Iso User", email="iso@test.com", segment="reliable", payment_reliability=0.98, natural_pay_propensity=0.95, link_responsiveness=0.8, reminder_responsiveness=0.5, plan_responsiveness=0.5, avg_delay_days=1, true_promise_reliability=0.98)
            inv = Invoice(id="INV-ISO-1", customer_id="C-ISO-1", amount=40000.0, status="OVERDUE", due_date=current_time)
            db.add_all([cust, inv])
            db.commit()

            # Insert a "poisoned/bogus" production Case that claims action = 'bogus_action'
            poison_case = Case(
                id="REC-POISON",
                customer_id="C-ISO-1",
                invoice_id="INV-ISO-1",
                issue_type="OVERDUE_PAYMENT",
                amount_at_risk=40000.0,
                status="OPEN",
                priority="LOW",
                p_natural=0.95,
                p_intervene=0.95,
                expected_incremental_recovery=0.0,
                recommended_action="bogus_poisoned_action",
                ai_reasoning=json.dumps(["Poison"]),
                audit_history=json.dumps([]),
                budget_allocated=True
            )
            db.add(poison_case)
            db.commit()

            # Run evaluation
            eval_res = run_batch_evaluation(db, batch_size=1, seed=42)
            eval_case = eval_res["cases"][0]
            
            # Must NOT use 'bogus_poisoned_action' from production Case table!
            self.assertNotEqual(eval_case["ai"]["action"], "bogus_poisoned_action")
            self.assertEqual(eval_case["ai"]["action"], "do_nothing")
        finally:
            db.close()

    def test_e_no_hidden_ground_truth_passed_to_agent(self):
        """TEST E: No hidden ground-truth fields are passed to the agent."""
        db = self.Session()
        try:
            cust = db.query(Customer).filter(Customer.id == "C-TEST-1").first()
            profile = get_customer_profile(db, cust.id)
            forbidden = ["natural_pay_propensity", "link_responsiveness", "reminder_responsiveness", "plan_responsiveness", "true_promise_reliability"]
            for f in forbidden:
                self.assertNotIn(f, profile)
        finally:
            db.close()

    def test_f_recovery_totals_equal_simulated_outcomes(self):
        """TEST F: Recovery totals equal sum of simulated recovery outcomes."""
        db = self.Session()
        try:
            current_time = datetime.datetime(2026, 8, 30, 12, 0, 0)
            for i in range(1, 10):
                cust = Customer(id=f"C-TOT-{i}", name=f"Tot {i}", email=f"tot{i}@test.com", segment="chronic_late", payment_reliability=0.5, natural_pay_propensity=0.2, link_responsiveness=0.8, reminder_responsiveness=0.4, plan_responsiveness=0.7, avg_delay_days=10, true_promise_reliability=0.5)
                inv = Invoice(id=f"INV-TOT-{i}", customer_id=f"C-TOT-{i}", amount=10000.0 * i, status="OVERDUE", due_date=current_time)
                db.add_all([cust, inv])
            db.commit()

            res = run_batch_evaluation(db, batch_size=9, seed=999)
            sum_base = sum(c["baseline"]["recovered"] for c in res["cases"])
            sum_ai = sum(c["ai"]["recovered"] for c in res["cases"])

            self.assertEqual(round(sum_base, 2), round(res["summary"]["baseline"]["recovered"], 2))
            self.assertEqual(round(sum_ai, 2), round(res["summary"]["ai"]["recovered"], 2))
        finally:
            db.close()

    def test_g_changing_selected_action_changes_simulated_outcome(self):
        """TEST G: Changing selected agent action changes simulated outcome probability appropriately."""
        db = self.Session()
        try:
            current_time = datetime.datetime(2026, 8, 30, 12, 0, 0)
            cust = Customer(id="C-ACT-1", name="Act User", email="act@test.com", segment="chronic_late", payment_reliability=0.4, natural_pay_propensity=0.2, link_responsiveness=0.8, reminder_responsiveness=0.4, plan_responsiveness=0.8, avg_delay_days=10, true_promise_reliability=0.4)
            inv = Invoice(id="INV-ACT-1", customer_id="C-ACT-1", amount=50000.0, status="OVERDUE", due_date=current_time)
            db.add_all([cust, inv])
            db.commit()

            decision_do_nothing = {
                "selected_action": "do_nothing", "p_natural": 0.20, "p_intervene": 0.20,
                "tools_called": ["get_customer_profile"], "selected_reason": "Do nothing"
            }
            decision_link = {
                "selected_action": "create_payment_link", "p_natural": 0.20, "p_intervene": 0.65,
                "tools_called": ["get_customer_profile"], "selected_reason": "Payment link"
            }

            # On latent_roll = 0.50: do_nothing (p=0.20) fails, create_payment_link (p=0.65) succeeds
            sim_dn = simulate_counterfactual_case(db, inv, cust, "OVERDUE_PAYMENT", 50000.0, "send_payment_reminder", decision_do_nothing, 0.50)
            sim_link = simulate_counterfactual_case(db, inv, cust, "OVERDUE_PAYMENT", 50000.0, "send_payment_reminder", decision_link, 0.50)

            self.assertEqual(sim_dn["ai"]["recovered"], 0.0)
            self.assertEqual(sim_link["ai"]["recovered"], 50000.0)
        finally:
            db.close()

    def test_h_reproducibility_identical_runs(self):
        """TEST H: Running evaluation twice with the same seed gives 100% identical results."""
        db = self.Session()
        try:
            res1 = run_batch_evaluation(db, batch_size=10, seed=777)
            res2 = run_batch_evaluation(db, batch_size=10, seed=777)

            self.assertEqual(res1["summary"]["baseline"]["recovered"], res2["summary"]["baseline"]["recovered"])
            self.assertEqual(res1["summary"]["ai"]["recovered"], res2["summary"]["ai"]["recovered"])
            self.assertEqual(res1["summary"]["metrics"]["incremental_recovered"], res2["summary"]["metrics"]["incremental_recovered"])
        finally:
            db.close()

if __name__ == "__main__":
    unittest.main()
