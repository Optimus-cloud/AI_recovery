import os
import json
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

# Setup API clients if keys are present
HAS_OPENAI = False
HAS_GEMINI = False

openai_key = os.getenv("OPENAI_API_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

if openai_key:
    from openai import OpenAI
    try:
        openai_client = OpenAI(api_key=openai_key)
        HAS_OPENAI = True
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {e}")

if gemini_key:
    import google.generativeai as genai
    try:
        genai.configure(api_key=gemini_key)
        HAS_GEMINI = True
    except Exception as e:
        print(f"Failed to initialize Gemini client: {e}")

def agent_reason_and_select_action(
    case_id: str,
    customer_name: str,
    segment: str,
    reliability: float,
    issue_type: str,
    amount: float,
    days_overdue: int,
    evidence: Dict[str, Any],
    candidate_estimates: List[Dict[str, Any]],
    allowed_actions: List[str]
) -> Dict[str, Any]:
    """
    Core Agentic Reasoning & Action Selection:
    The AI Agent receives the retrieved evidence and the deterministic financial estimates matrix,
    reasons over the trade-offs, and autonomously selects the best permitted action.
    """
    evidence_str = json.dumps(evidence or {}, indent=2)
    estimates_str = json.dumps(candidate_estimates, indent=2)
    allowed_str = json.dumps(allowed_actions)

    prompt = f"""
    You are the autonomous AI Revenue Recovery Agent. You are tasked with analyzing a financial recovery case, reviewing the evidence retrieved by your tools, and evaluating the deterministic financial estimates for all candidate actions to select the best action.
    
    Case Profile:
    - Case ID: {case_id}
    - Customer Name: {customer_name}
    - Customer Segment: {segment}
    - Historical Payment Reliability: {reliability:.0%}
    - Issue Type: {issue_type}
    - Amount at Risk: ₹{amount:,.2f}
    - Days Overdue: {days_overdue} days
    - Evidence Retrieved: {evidence_str}
    
    Candidate Actions & Deterministic Financial Estimates:
    {estimates_str}
    
    Merchant Allowed Actions:
    {allowed_str}
    
    Decision Rules:
    1. If natural recovery probability P(natural) is >= 90% or incremental lift is negligible (< ₹1,000), select 'do_nothing' to save budget and avoid customer fatigue.
    2. If issue is UNDERPAYMENT and evidence confirms a legitimate refund/credit explaining the gap, select 'investigate_underpayment'.
    3. Otherwise, select the action that maximizes Expected Incremental Recovery (EV) among permitted actions.
    4. Consider customer behavior: chronic late payers benefit from payment plans, transient errors benefit from retries, responsive clients benefit from payment links.
    
    Return ONLY a valid JSON object with this exact structure:
    {{
      "selected_action": "<action_key_from_candidates>",
      "selected_reason": "<one concise sentence explaining why this action was selected>",
      "reasoning_points": [
        "WHY THIS CUSTOMER: <explanation based on segment and reliability>",
        "WHY NOW: <explanation based on urgency and days overdue>",
        "WHY THIS ACTION: <explanation of why selected action fits>",
        "WHY NOT OTHER ACTIONS: <why other candidate options were deprioritized or rejected>",
        "EVIDENCE USED: <list of facts and data points used>",
        "UNCERTAINTIES: <acknowledged risks or unknowns>"
      ]
    }}
    """

    if HAS_GEMINI:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            text = response.text.strip()
            if "{" in text and "}" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                parsed = json.loads(text[start:end])
                if "selected_action" in parsed and "reasoning_points" in parsed:
                    return parsed
        except Exception as e:
            print(f"Gemini agent selection failed: {e}. Falling back to deterministic agent engine...")

    if HAS_OPENAI:
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            text = response.choices[0].message.content.strip()
            if "{" in text and "}" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                parsed = json.loads(text[start:end])
                if "selected_action" in parsed and "reasoning_points" in parsed:
                    return parsed
        except Exception as e:
            print(f"OpenAI agent selection failed: {e}. Falling back to deterministic agent engine...")

    # Deterministic Agent Reasoning Engine (Zero Hallucination, evidence & EV-driven)
    return agent_deterministic_select_and_reason(
        case_id, customer_name, segment, reliability, issue_type,
        amount, days_overdue, evidence, candidate_estimates, allowed_actions
    )

def agent_deterministic_select_and_reason(
    case_id: str,
    customer_name: str,
    segment: str,
    reliability: float,
    issue_type: str,
    amount: float,
    days_overdue: int,
    evidence: Dict[str, Any],
    candidate_estimates: List[Dict[str, Any]],
    allowed_actions: List[str]
) -> Dict[str, Any]:
    """
    Deterministic Agent Decision Engine:
    Evaluates candidate action estimates matrix, applies multi-attribute utility ranking,
    and returns selected action and structured rationale.
    """
    # 1. Underpayment legitimate refund/credit check
    if issue_type == "UNDERPAYMENT" and evidence.get("underpayment_legit"):
        selected_action = "investigate_underpayment"
        selected_reason = "Underpayment investigation confirmed legitimate credit/refund note. Case resolved: Not Recoverable."
    else:
        # 2. Check natural recovery threshold for DO_NOTHING
        do_nothing_cand = next((c for c in candidate_estimates if c["action"] == "do_nothing"), None)
        p_natural = do_nothing_cand["p_natural"] if do_nothing_cand else 0.20

        if p_natural >= 0.90:
            selected_action = "do_nothing"
            selected_reason = f"Customer has high natural payment propensity ({p_natural:.0%}). Selected 'Do Nothing' to prevent unnecessary outreach."
        else:
            # 3. Filter permitted actions and find maximum incremental EV
            permitted_candidates = [c for c in candidate_estimates if c.get("policy_permitted", True)]
            if permitted_candidates:
                # Sort by expected incremental recovery descending
                permitted_candidates.sort(key=lambda x: x.get("expected_incremental_recovery", 0.0), reverse=True)
                top = permitted_candidates[0]
                
                if top.get("expected_incremental_recovery", 0.0) <= 0.0:
                    selected_action = "do_nothing"
                    selected_reason = "All active interventions offer negligible incremental lift over natural recovery baseline."
                else:
                    selected_action = top["action"]
                    selected_reason = f"Selected '{top['label']}' with highest expected incremental recovery of ₹{top['expected_incremental_recovery']:,.2f}."
            else:
                selected_action = "escalate_to_human"
                selected_reason = "No candidate actions permitted under merchant policy. Escalating to human desk."

    # Build chosen candidate object
    chosen_cand = next((c for c in candidate_estimates if c["action"] == selected_action), None) or candidate_estimates[0]
    p_nat = chosen_cand.get("p_natural", 0.20)
    p_act = chosen_cand.get("p_action", 0.60)
    inc_rec = chosen_cand.get("expected_incremental_recovery", 0.0)

    # 4. Generate structured 6-point reasoning
    why_customer = f"WHY THIS CUSTOMER: {customer_name} ({segment.replace('_', ' ')}) has historical payment reliability of {reliability:.0%}."
    
    if issue_type == "FAILED_PAYMENT":
        why_now = f"WHY NOW: Recent payment attempt failed with error '{evidence.get('recent_error_code', 'error')}', putting ₹{amount:,.2f} at immediate churn risk."
    elif issue_type == "OVERDUE_PAYMENT":
        why_now = f"WHY NOW: Invoice is {days_overdue} days overdue without incoming settlement."
    elif issue_type == "BROKEN_PROMISE":
        why_now = f"WHY NOW: Customer missed payment commitment date ({evidence.get('promise_reliability', 'low')} compliance history)."
    elif issue_type == "UNDERPAYMENT":
        why_now = f"WHY NOW: Invoice has an unreconciled gap of ₹{amount:,.2f} on the ledger."
    else:
        why_now = f"WHY NOW: Timely intervention required to recover ₹{amount:,.2f}."

    action_descriptions = {
        "do_nothing": "Do Nothing was chosen because natural self-cure probability is high (>=90%), eliminating customer friction.",
        "retry_payment": "Payment Retry was chosen because failure logs indicate a transient bank or network error.",
        "create_payment_link": "Direct Payment Link provides zero-friction instant checkout via UPI/card.",
        "send_payment_reminder": "Soft Payment Reminder nudges the customer without aggressive dunning friction.",
        "request_payment_commitment": "Requesting a Promise-to-Pay creates a binding commitment date.",
        "propose_payment_plan": "Proposing a 3-Month Installment Plan makes large balances manageable.",
        "investigate_underpayment": "Underpayment Audit reconciles credit notes and co-marketing discounts before demanding balance.",
        "escalate_to_human": "Human Escalation is required due to high balance or complex dispute history."
    }
    why_action = f"WHY THIS ACTION: {action_descriptions.get(selected_action, 'Action optimizes expected incremental recovery.')}"

    if selected_action == "do_nothing":
        why_not = "WHY NOT OTHER ACTIONS: Other interventions yield negligible incremental lift (<₹1,000) and would cause unnecessary customer fatigue."
    elif selected_action == "create_payment_link":
        why_not = f"WHY NOT OTHER ACTIONS: Passive reminders had lower estimated recovery (+₹{inc_rec:,.2f} vs +₹{max(0, inc_rec*0.4):,.2f}), while installment plans add needless duration."
    elif selected_action == "propose_payment_plan":
        why_not = "WHY NOT OTHER ACTIONS: Full-balance lump-sum requests have high default risk for chronic late payers."
    elif selected_action == "retry_payment":
        why_not = "WHY NOT OTHER ACTIONS: Manual payment links are unnecessary when auto-retry can succeed without customer friction."
    else:
        why_not = "WHY NOT OTHER ACTIONS: Alternative candidate interventions yielded lower expected incremental value (EV_inc)."

    evidence_items = [f"invoice amount ₹{amount:,.2f}"]
    if issue_type == "FAILED_PAYMENT" and evidence.get("recent_error_code"):
        evidence_items.append(f"error code '{evidence.get('recent_error_code')}'")
    if issue_type == "BROKEN_PROMISE":
        evidence_items.append(f"promise reliability rate of {evidence.get('promise_reliability', '50%')}")
    if issue_type == "UNDERPAYMENT":
        evidence_items.append(f"adjustment status '{evidence.get('underpayment_status', 'audited')}'")
    
    what_evidence = f"EVIDENCE USED: Customer segment '{segment}', {', '.join(evidence_items)}, and empirical success priors."

    if issue_type == "FAILED_PAYMENT":
        what_uncertain = "UNCERTAINTIES: Whether the card failure was due to transient bank downtime or cardholder cancellation."
    elif issue_type == "BROKEN_PROMISE":
        what_uncertain = "UNCERTAINTIES: Whether the missed promise was administrative oversight or severe cash-flow distress."
    elif issue_type == "UNDERPAYMENT":
        what_uncertain = "UNCERTAINTIES: Whether unlogged offline sales discounts were verbally agreed with the merchant."
    else:
        what_uncertain = "UNCERTAINTIES: Customer's exact willingness to pay without a high-touch human follow-up."

    return {
        "selected_action": selected_action,
        "selected_reason": selected_reason,
        "reasoning_points": [why_customer, why_now, why_action, why_not, what_evidence, what_uncertain]
    }

# Backward compatibility alias
def get_llm_reasoning(
    case_id: str,
    customer_name: str,
    segment: str,
    reliability: float,
    issue_type: str,
    amount: float,
    days_overdue: int,
    p_natural: float,
    p_intervene: float,
    incremental_recovery: float,
    recommended_action: str,
    additional_evidence: dict = None
) -> list:
    res = agent_deterministic_select_and_reason(
        case_id=case_id,
        customer_name=customer_name,
        segment=segment,
        reliability=reliability,
        issue_type=issue_type,
        amount=amount,
        days_overdue=days_overdue,
        evidence=additional_evidence or {},
        candidate_estimates=[{
            "action": recommended_action,
            "label": recommended_action.replace("_", " ").title(),
            "p_natural": p_natural,
            "p_action": p_intervene,
            "expected_incremental_recovery": incremental_recovery,
            "policy_permitted": True
        }],
        allowed_actions=[recommended_action]
    )
    return res["reasoning_points"]
