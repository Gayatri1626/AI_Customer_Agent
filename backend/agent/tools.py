"""
Tools available to the LangGraph refund agent.
"""
import json
from datetime import date
from langchain_core.tools import tool
from data.crm_database import (
    get_customer_by_id,
    get_customer_by_email,
    get_order_by_id,
    list_all_customers,
)
from data.refund_policy import get_policy_text, get_policy_rules

TODAY = date.today()


@tool
def lookup_customer(identifier: str) -> str:
    """
    Look up a customer by their customer ID (e.g. C001) or email address.
    Returns customer profile including tier and contact details.
    """
    customer = get_customer_by_id(identifier) or get_customer_by_email(identifier)
    if not customer:
        return json.dumps({"error": f"No customer found for identifier: {identifier}"})
    # Return without orders to keep response concise; use get_order_details for orders
    summary = {k: v for k, v in customer.items() if k != "orders"}
    summary["order_ids"] = [o["order_id"] for o in customer["orders"]]
    return json.dumps(summary)


@tool
def get_order_details(order_id: str) -> str:
    """
    Retrieve full details of a specific order by its order ID (e.g. ORD-10021).
    Returns product, category, amount, purchase date, condition, and return reason.
    """
    customer, order = get_order_by_id(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found."})
    return json.dumps({
        "customer_id": customer["id"],
        "customer_name": customer["name"],
        "customer_tier": customer["tier"],
        **order,
    })


@tool
def get_refund_policy() -> str:
    """
    Retrieve the full ShopEase refund & return policy document.
    Call this to understand the rules before making a refund decision.
    """
    return get_policy_text()


@tool
def validate_refund_eligibility(order_id: str) -> str:
    """
    Validate whether an order is eligible for a refund based on policy rules.
    Returns eligibility status, reason, applicable return window, and refund method.
    """
    customer, order = get_order_by_id(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found."})

    rules = get_policy_rules()
    category = order["category"]
    condition = order["condition"]
    purchase_date = date.fromisoformat(order["purchase_date"])
    days_since_purchase = (TODAY - purchase_date).days
    tier = customer["tier"]

    # Determine return window for this category
    window = rules["return_windows_days"].get(category, rules["return_windows_days"]["default"])
    if tier == "Gold":
        window += rules["gold_tier_bonus_days"]

    reasoning_steps = []

    # --- Rule 1: Non-refundable categories ---
    if category in rules["non_refundable_categories"]:
        return json.dumps({
            "eligible": False,
            "reason": f"'{category}' items are non-refundable once accessed or downloaded (Policy §3a).",
            "days_since_purchase": days_since_purchase,
            "return_window_days": window,
            "refund_method": "None",
        })

    # --- Rule 2: Defective / damaged — always refundable within 30 days ---
    if condition == "Defective" or "defective" in condition.lower():
        if days_since_purchase <= rules["defective_always_refundable_within_days"]:
            refund_method = (
                rules["refund_method"]["within_7_days"]
                if days_since_purchase <= 7
                else rules["refund_method"]["8_to_30_days"]
            )
            return json.dumps({
                "eligible": True,
                "reason": f"Item is defective. Defective items are fully refundable within 30 days (Policy §2, §7). Days elapsed: {days_since_purchase}.",
                "days_since_purchase": days_since_purchase,
                "return_window_days": 30,
                "refund_method": refund_method,
                "shipping": rules["shipping"]["defective_or_wrong_item"],
            })
        else:
            return json.dumps({
                "eligible": False,
                "reason": f"Item is defective but return window (30 days) has expired. Days elapsed: {days_since_purchase}.",
                "days_since_purchase": days_since_purchase,
                "return_window_days": 30,
                "refund_method": "None",
            })

    # --- Rule 3: Return window expired ---
    if days_since_purchase > window:
        return json.dumps({
            "eligible": False,
            "reason": f"Return window expired. Category '{category}' allows {window} days (Gold +5 applied if applicable). Days elapsed: {days_since_purchase}.",
            "days_since_purchase": days_since_purchase,
            "return_window_days": window,
            "refund_method": "None",
        })

    # --- Rule 4: Opened consumables ---
    if category in rules["opened_consumable_non_refundable"] and "Opened" in condition:
        return json.dumps({
            "eligible": False,
            "reason": f"Opened '{category}' items are non-refundable (Policy §3b). Reason given: '{order.get('reason_for_return', 'N/A')}'.",
            "days_since_purchase": days_since_purchase,
            "return_window_days": window,
            "refund_method": "None",
        })

    # --- Rule 5: Opened beauty products ---
    if category == "Beauty" and "Opened" in condition:
        reason = order.get("reason_for_return", "")
        if "allergic" in reason.lower() and days_since_purchase <= rules["allergic_reaction_window_days"]:
            refund_method = rules["refund_method"]["within_7_days"]
            return json.dumps({
                "eligible": True,
                "reason": f"Allergic reaction reported within 7-day window (Policy §7). Days elapsed: {days_since_purchase}.",
                "days_since_purchase": days_since_purchase,
                "return_window_days": rules["allergic_reaction_window_days"],
                "refund_method": refund_method,
                "note": "Photo evidence required per policy.",
                "shipping": rules["shipping"]["defective_or_wrong_item"],
            })
        else:
            return json.dumps({
                "eligible": False,
                "reason": f"Opened beauty products are non-refundable (Policy §3c), unless within 7-day allergic reaction window. Days elapsed: {days_since_purchase}.",
                "days_since_purchase": days_since_purchase,
                "return_window_days": window,
                "refund_method": "None",
            })

    # --- Rule 6: Worn / used items (non-defective) ---
    if condition in ("Worn", "Used") and condition != "Defective":
        return json.dumps({
            "eligible": False,
            "reason": f"Worn or used items are not eligible for refund unless defective (Policy §2). Condition: '{condition}'.",
            "days_since_purchase": days_since_purchase,
            "return_window_days": window,
            "refund_method": "None",
        })

    # --- Rule 7: Wrong item received ---
    reason = order.get("reason_for_return", "")
    if "wrong" in reason.lower() and "received" in reason.lower():
        refund_method = (
            rules["refund_method"]["within_7_days"]
            if days_since_purchase <= 7
            else rules["refund_method"]["8_to_30_days"]
        )
        return json.dumps({
            "eligible": True,
            "reason": f"Wrong item received. Full refund or free exchange (Policy §7). Days elapsed: {days_since_purchase}.",
            "days_since_purchase": days_since_purchase,
            "return_window_days": window,
            "refund_method": refund_method,
            "shipping": rules["shipping"]["defective_or_wrong_item"],
        })

    # --- Default: Eligible within window ---
    refund_method = (
        rules["refund_method"]["within_7_days"]
        if days_since_purchase <= 7
        else rules["refund_method"]["8_to_30_days"]
    )
    shipping = (
        rules["shipping"]["defective_or_wrong_item"]
        if "wrong" in reason.lower()
        else rules["shipping"]["change_of_mind"]
    )
    return json.dumps({
        "eligible": True,
        "reason": f"Item is within the {window}-day return window and meets condition requirements (Policy §1–2). Days elapsed: {days_since_purchase}.",
        "days_since_purchase": days_since_purchase,
        "return_window_days": window,
        "refund_method": refund_method,
        "shipping": shipping,
    })


@tool
def approve_refund(order_id: str, refund_method: str, notes: str = "") -> str:
    """
    Approve a refund for the given order. Specify the refund method and any notes.
    This records the decision in the session.
    """
    customer, order = get_order_by_id(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found."})
    return json.dumps({
        "decision": "APPROVED",
        "order_id": order_id,
        "product": order["product"],
        "amount": order["amount"],
        "refund_method": refund_method,
        "notes": notes,
        "message": f"Refund of ${order['amount']:.2f} approved via {refund_method}. {notes}".strip(),
    })


@tool
def deny_refund(order_id: str, reason: str) -> str:
    """
    Deny a refund request for the given order with a clear policy-based reason.
    """
    customer, order = get_order_by_id(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found."})
    return json.dumps({
        "decision": "DENIED",
        "order_id": order_id,
        "product": order["product"],
        "amount": order["amount"],
        "reason": reason,
        "message": f"Refund denied. {reason}",
    })


@tool
def list_customers() -> str:
    """
    List all customers in the CRM (id, name, email, tier). Useful for admin queries.
    """
    customers = list_all_customers()
    summary = [
        {"id": c["id"], "name": c["name"], "email": c["email"], "tier": c["tier"]}
        for c in customers
    ]
    return json.dumps(summary)


ALL_TOOLS = [
    lookup_customer,
    get_order_details,
    get_refund_policy,
    validate_refund_eligibility,
    approve_refund,
    deny_refund,
    list_customers,
]
