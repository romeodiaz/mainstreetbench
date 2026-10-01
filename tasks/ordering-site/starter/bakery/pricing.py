"""Order pricing: subtotal, promo discount, sales tax and total."""

TAX_RATE = 0.08


def price_order(lines: list, promo) -> dict:
    """lines: [{"qty", "unit_price"}]; promo: a promo_codes row or None."""
    subtotal = round(sum(line["qty"] * line["unit_price"] for line in lines), 2)
    tax = round(subtotal * TAX_RATE, 2)
    discount = 0.0
    if promo is not None:
        if promo["percent_off"]:
            discount = round(subtotal * promo["percent_off"] / 100, 2)
        elif promo["amount_off"]:
            discount = min(promo["amount_off"], subtotal)
    total = round(subtotal - discount + tax, 2)
    return {"subtotal": subtotal, "discount": discount, "tax": tax, "total": total}
