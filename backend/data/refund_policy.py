"""
Strict Refund Policy — used by the agent to validate refund requests.
"""

REFUND_POLICY_TEXT = """
# ShopEase Refund & Return Policy (v2.1 – Effective June 2024)

## 1. Return Window
- Standard items: 30 days from delivery date.
- Electronics: 15 days from delivery date.
- Clothing & Footwear: 30 days from delivery date (items must be unworn and have original tags).
- Health, Nutrition & Beauty (opened): NON-REFUNDABLE once opened, except for proven allergic reactions.
- Digital Goods (downloads, licenses, subscriptions): NON-REFUNDABLE once accessed or downloaded.

## 2. Item Condition Requirements
- Unopened / Sealed: Full refund always eligible within return window.
- Opened (non-consumable): Eligible for refund only if defective or if item received differs from order (wrong item).
- Worn / Used: NOT eligible for refund unless item is defective or damaged upon arrival.
- Defective / Damaged on arrival: Full refund eligible at any time within 30 days of delivery, regardless of category.

## 3. Non-Refundable Categories
The following are NEVER eligible for refunds:
  a. Digital goods once accessed or downloaded.
  b. Opened consumables (food, protein powders, vitamins, supplements) — unless sealed and unopened.
  c. Opened beauty / personal care products — exception: documented allergic reaction within 7 days of purchase.
  d. Gift cards and store credit.
  e. Items returned after the applicable return window has expired.

## 4. Refund Method
- Original payment method if within 7 days of purchase.
- Store credit only if between 8–30 days of purchase (or 8–15 days for electronics).
- No refund outside the return window.

## 5. Shipping Costs
- Defective / wrong item: ShopEase covers return shipping.
- Change of mind / preference: Customer covers return shipping ($7.99 flat rate deducted from refund).

## 6. Loyalty Tier Benefits
- Gold members: +5 extra days added to the standard return window.
- Silver members: Standard policy applies.
- Bronze members: Standard policy applies.

## 7. Special Circumstances
- Allergic reactions (Beauty/Health): Refundable within 7 days of purchase with photo evidence.
- Wrong item received: Full refund or free exchange, ShopEase covers return shipping.
- Item never arrived (lost in transit): Full refund regardless of time elapsed, after carrier investigation.

## 8. Process
- Refunds are processed within 5–7 business days after item is received.
- Store credit is issued within 24 hours.
- Customers must initiate a return request before shipping items back.
"""

POLICY_RULES = {
    "return_windows_days": {
        "default": 30,
        "Electronics": 15,
        "Clothing": 30,
        "Footwear": 30,
        "Beauty": 30,
        "Health & Nutrition": 30,
        "Kitchen": 30,
        "Sports": 30,
        "Accessories": 30,
        "Digital Goods": 0,  # non-refundable once accessed
    },
    "gold_tier_bonus_days": 5,
    "non_refundable_categories": ["Digital Goods"],
    "opened_consumable_non_refundable": ["Health & Nutrition"],
    "opened_beauty_non_refundable": True,
    "allergic_reaction_window_days": 7,
    "defective_always_refundable_within_days": 30,
    "refund_method": {
        "within_7_days": "Original payment method",
        "8_to_30_days": "Store credit only",
        "after_window": "No refund",
    },
    "shipping": {
        "defective_or_wrong_item": "ShopEase covers return shipping",
        "change_of_mind": "$7.99 deducted from refund",
    },
}


def get_policy_text() -> str:
    return REFUND_POLICY_TEXT


def get_policy_rules() -> dict:
    return POLICY_RULES
