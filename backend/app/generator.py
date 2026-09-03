import random
import datetime
from sqlalchemy.orm import Session
from .database import engine, Base, SessionLocal
from .models import (
    Customer, Invoice, PaymentAttempt, Promise, AdjustmentRefund,
    PolicySettings, Case, AuditLog, RecoveryTransaction, InterventionFeedback
)
import json

# Set seed for reproducibility
random.seed(42)

def generate_synthetic_data(db: Session):
    print("Clearing existing data...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("Generating Policy Settings...")
    policy = PolicySettings(
        id="default",
        auto_approve_threshold=10000.0,
        audit_log_threshold=10000.0,
        require_approval_threshold=100000.0,
        allowed_actions=json.dumps([
            "do_nothing",
            "retry_payment",
            "create_payment_link",
            "send_payment_reminder",
            "request_payment_commitment",
            "propose_payment_plan",
            "investigate_underpayment",
            "escalate_to_human"
        ]),
        max_discount_rate=0.15,
        daily_limit=50,
        daily_intervention_budget=30,
        intervention_cost_penalty=50.0
    )
    db.add(policy)
    db.commit()

    print("Generating 1,500 Customers with Latent Ground Truth...")
    segments = ["reliable", "occasional_late", "chronic_late", "broken_promise", "partial_payer"]
    segment_weights = [0.65, 0.18, 0.09, 0.05, 0.03]

    customer_names = [
        "Aarav Sharma", "Aditya Patel", "Ananya Iyer", "Arjun Mehta", "Avani Sen", 
        "Devendra Verma", "Diya Rao", "Ishaan Nair", "Kavya Reddy", "Krishna Pillai",
        "Mira Joshi", "Nikhil Gupta", "Pranav Deshmukh", "Rohan Kulkarni", "Saanvi Bhatt",
        "Siddharth Roy", "Tanvi Dixit", "Varun Bose", "Yash Choudhury", "Zoya Khan",
        "Acme Corp India", "Bharatiya Retail", "Chennai Logistics", "Deccan Enterprises",
        "Ganges Tech Solutions", "Himalaya Healthcare", "Indus Infratech", "Kerala Spices Ltd",
        "Mumbai Fintech Partners", "Punjab Agro Industries"
    ]
    
    customers = []
    for i in range(1, 1501):
        segment = random.choices(segments, weights=segment_weights)[0]
        
        # Ground Truth Latent Attributes
        if segment == "reliable":
            reliability = random.uniform(0.92, 0.99)
            nat_propensity = random.uniform(0.88, 0.98)
            link_resp = random.uniform(0.85, 0.99)
            rem_resp = random.uniform(0.70, 0.90)
            plan_resp = random.uniform(0.30, 0.60)
            avg_delay = random.randint(0, 3)
            true_prm = random.uniform(0.90, 0.99)
        elif segment == "occasional_late":
            reliability = random.uniform(0.75, 0.90)
            nat_propensity = random.uniform(0.60, 0.80)
            link_resp = random.uniform(0.75, 0.90)
            rem_resp = random.uniform(0.60, 0.80)
            plan_resp = random.uniform(0.50, 0.75)
            avg_delay = random.randint(4, 10)
            true_prm = random.uniform(0.70, 0.88)
        elif segment == "chronic_late":
            reliability = random.uniform(0.40, 0.70)
            nat_propensity = random.uniform(0.15, 0.35)
            link_resp = random.uniform(0.50, 0.70)
            rem_resp = random.uniform(0.30, 0.50)
            plan_resp = random.uniform(0.70, 0.90)
            avg_delay = random.randint(12, 35)
            true_prm = random.uniform(0.35, 0.65)
        elif segment == "broken_promise":
            reliability = random.uniform(0.30, 0.60)
            nat_propensity = random.uniform(0.10, 0.25)
            link_resp = random.uniform(0.40, 0.65)
            rem_resp = random.uniform(0.20, 0.40)
            plan_resp = random.uniform(0.65, 0.85)
            avg_delay = random.randint(15, 45)
            true_prm = random.uniform(0.15, 0.45)
        else: # partial_payer
            reliability = random.uniform(0.50, 0.85)
            nat_propensity = random.uniform(0.30, 0.55)
            link_resp = random.uniform(0.65, 0.85)
            rem_resp = random.uniform(0.45, 0.65)
            plan_resp = random.uniform(0.75, 0.95)
            avg_delay = random.randint(8, 25)
            true_prm = random.uniform(0.50, 0.80)

        name_base = random.choice(customer_names)
        is_corp = "Corp" in name_base or "Enterprises" in name_base or "Solutions" in name_base or "Ltd" in name_base or "Partners" in name_base or "Retail" in name_base or "Logistics" in name_base or "Healthcare" in name_base or "Infratech" in name_base or "Agro" in name_base
        
        if is_corp:
            name = f"{name_base} (Batch {i})"
        else:
            name = f"{name_base} {random.randint(100, 999)}"

        cust = Customer(
            id=f"C-{1000 + i}",
            name=name,
            email=f"{name.lower().replace(' ', '.').replace('(', '').replace(')', '')}@example.com",
            segment=segment,
            payment_reliability=round(reliability, 2),
            natural_pay_propensity=round(nat_propensity, 2),
            link_responsiveness=round(link_resp, 2),
            reminder_responsiveness=round(rem_resp, 2),
            plan_responsiveness=round(plan_resp, 2),
            avg_delay_days=avg_delay,
            true_promise_reliability=round(true_prm, 2),
            created_at=datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(100, 365))
        )
        db.add(cust)
        customers.append(cust)

    db.commit()
    print(f"Generated {len(customers)} customers.")

    print("Generating Invoices, Payments, Promises, Adjustments...")
    current_time = datetime.datetime(2026, 8, 30, 12, 0, 0)
    invoice_counter = 10000
    attempt_counter = 50000
    promise_counter = 30000
    adj_counter = 70000

    invoices = []
    
    for cust in customers:
        # Determine number of invoices per customer (ensures 1,000+ at-risk invoices for scaling tests)
        if "Corp" in cust.name or "Enterprises" in cust.name:
            num_invoices = random.randint(5, 10)
        else:
            num_invoices = random.randint(3, 7)

        for inv_idx in range(num_invoices):
            invoice_counter += 1
            inv_id = f"INV-{invoice_counter}"
            
            # Amount based on customer type
            if "Corp" in cust.name or "Enterprises" in cust.name:
                amount = round(random.uniform(50000, 500000), 2)
            else:
                amount = round(random.uniform(2000, 45000), 2)

            created_days_ago = random.randint(10, 120)
            inv_created = current_time - datetime.timedelta(days=created_days_ago)
            due_days = 30
            inv_due = inv_created + datetime.timedelta(days=due_days)

            # Determine invoice state
            roll = random.random()
            if roll < cust.payment_reliability:
                # Paid invoice
                status = "PAID"
                inv = Invoice(
                    id=inv_id,
                    customer_id=cust.id,
                    amount=amount,
                    status=status,
                    due_date=inv_due,
                    created_at=inv_created
                )
                db.add(inv)
                
                # Successful payment attempt
                attempt_counter += 1
                att = PaymentAttempt(
                    id=f"ATT-{attempt_counter}",
                    invoice_id=inv_id,
                    amount=amount,
                    status="SUCCESS",
                    created_at=inv_created + datetime.timedelta(days=random.randint(5, due_days + cust.avg_delay_days))
                )
                db.add(att)
                
            else:
                # Issue Invoice (Unpaid, Overdue, Failed, Partial)
                if cust.segment == "partial_payer":
                    status = "PARTIAL"
                    paid_part = round(amount * random.uniform(0.40, 0.85), 2)
                    inv = Invoice(
                        id=inv_id,
                        customer_id=cust.id,
                        amount=amount,
                        status=status,
                        due_date=inv_due,
                        created_at=inv_created
                    )
                    db.add(inv)
                    
                    attempt_counter += 1
                    att = PaymentAttempt(
                        id=f"ATT-{attempt_counter}",
                        invoice_id=inv_id,
                        amount=paid_part,
                        status="SUCCESS",
                        created_at=inv_due - datetime.timedelta(days=random.randint(1, 5))
                    )
                    db.add(att)

                    # 40% of partials have a legitimate adjustment credit
                    if random.random() < 0.40:
                        adj_counter += 1
                        adj = AdjustmentRefund(
                            id=f"ADJ-{adj_counter}",
                            invoice_id=inv_id,
                            amount=round(amount - paid_part, 2),
                            type="DISCOUNT",
                            reason="Co-marketing promotional credit applied offline",
                            created_at=inv_due
                        )
                        db.add(adj)

                elif cust.segment == "broken_promise":
                    status = "OVERDUE"
                    inv = Invoice(
                        id=inv_id,
                        customer_id=cust.id,
                        amount=amount,
                        status=status,
                        due_date=inv_due,
                        created_at=inv_created
                    )
                    db.add(inv)
                    
                    # Broken promise record
                    promise_counter += 1
                    prm = Promise(
                        id=f"PRM-{promise_counter}",
                        customer_id=cust.id,
                        invoice_id=inv_id,
                        promised_amount=amount,
                        promised_date=current_time - datetime.timedelta(days=random.randint(2, 10)),
                        status="BROKEN",
                        created_at=inv_due
                    )
                    db.add(prm)

                else: # Failed payment or regular overdue
                    is_failed_attempt = random.random() < 0.60
                    status = "OVERDUE" if inv_due < current_time else "UNPAID"
                    inv = Invoice(
                        id=inv_id,
                        customer_id=cust.id,
                        amount=amount,
                        status=status,
                        due_date=inv_due,
                        created_at=inv_created
                    )
                    db.add(inv)

                    if is_failed_attempt:
                        attempt_counter += 1
                        err = random.choice(["network_error", "insufficient_funds", "expired_card"])
                        att = PaymentAttempt(
                            id=f"ATT-{attempt_counter}",
                            invoice_id=inv_id,
                            amount=amount,
                            status="FAILED",
                            error_code=err,
                            created_at=current_time - datetime.timedelta(days=random.randint(1, 7))
                        )
                        db.add(att)

            invoices.append(inv)

    db.commit()
    print(f"Generated {len(invoices)} invoices.")

    print("Generating Historical Outcome Feedback Records (Learning Priors)...")
    feedback_actions = ["retry_payment", "create_payment_link", "send_payment_reminder", "request_payment_commitment", "propose_payment_plan", "investigate_underpayment"]
    issue_types = ["FAILED_PAYMENT", "OVERDUE_PAYMENT", "BROKEN_PROMISE", "UNDERPAYMENT"]
    
    feedbacks = []
    for _ in range(250):
        c = random.choice(customers)
        issue = random.choice(issue_types)
        act = random.choice(feedback_actions)
        
        # Determine success probability based on action + issue compatibility
        if issue == "FAILED_PAYMENT" and act == "retry_payment":
            succ_p = 0.85
        elif issue == "UNDERPAYMENT" and act == "investigate_underpayment":
            succ_p = 0.92
        elif issue == "BROKEN_PROMISE" and act == "propose_payment_plan":
            succ_p = 0.78
        elif act == "create_payment_link":
            succ_p = 0.70
        elif act == "send_payment_reminder":
            succ_p = 0.40
        else:
            succ_p = 0.50

        is_succ = random.random() < succ_p
        fb = InterventionFeedback(
            customer_id=c.id,
            customer_segment=c.segment,
            issue_type=issue,
            action=act,
            amount=round(random.uniform(5000, 100000), 2),
            outcome="SUCCESS" if is_succ else "FAILED",
            success=is_succ,
            time_to_payment_days=random.randint(1, 5) if is_succ else 0,
            created_at=current_time - datetime.timedelta(days=random.randint(1, 60))
        )
        db.add(fb)
        feedbacks.append(fb)

    db.commit()
    print(f"Generated {len(feedbacks)} historical feedback trials.")
    print("Database seeding completed successfully.")
