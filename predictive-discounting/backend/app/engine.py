from datetime import date
from typing import List

DISCOUNT_OPTIONS = (10, 15, 20)

def predict_demand(recent_sales: List[int], days_remaining: int) -> float:
    if not recent_sales:
        return 0.0
    weights = list(range(1, len(recent_sales) + 1))
    avg = sum(s * w for s, w in zip(recent_sales, weights)) / sum(weights)
    return round(avg * max(days_remaining, 1), 2)

def days_to_expiry(expiry_date: date, today: date) -> int:
    if not expiry_date:
        return 999
    return max((expiry_date - today).days, 0)

def compute_risk_score(stock_quantity: int, predicted_demand: float, days_remaining: int) -> float:
    if stock_quantity <= 0:
        return 0.0
    surplus = max(0.0, (stock_quantity - predicted_demand) / stock_quantity)
    urgency = 1.0 if days_remaining <= 3 else 0.6 if days_remaining <= 7 else 0.2
    return round(min(1.0, surplus * (0.7 + 0.3 * urgency)), 4)

def risk_level(score: float) -> str:
    if score >= 0.60:
        return "HIGH"
    if score >= 0.35:
        return "MEDIUM"
    return "LOW"

def discount_range(score: float, days_remaining: int):
    # Business-approved recommendation range is always 10%-20% for actionable risk.
    if score >= 0.60 or days_remaining <= 2:
        return (15, 20)
    if score >= 0.35 or days_remaining <= 5:
        return (10, 20)
    return (10, 15)

def recommended_price(mrp: float, discount_pct: float, expired: bool = False) -> float:
    if expired:
        return 0.0
    return round(min(mrp, mrp * (1 - discount_pct / 100)), 2)
