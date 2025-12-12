from decimal import Decimal, ROUND_HALF_UP

def round_currency(amount: float) -> float:
    """Rounds a float to 2 decimal places using standard rounding."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
