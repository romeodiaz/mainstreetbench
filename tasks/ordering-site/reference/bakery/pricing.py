"""Order pricing: subtotal, promo discount, sales tax and total.

Food (everything but gift cards) can be discounted and is taxed after the
discount. Gift cards are never discounted or taxed. Cents round half up.
"""

from decimal import Decimal, ROUND_HALF_UP

TAX_RATE = Decimal("0.08")
UNTAXED_CATEGORIES = {"Gift Cards"}
CENT = Decimal("0.01")


def to_cents(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def price_order(lines: list, promo) -> dict:
    """lines: [{"qty", "unit_price", "category"}]; promo: a promo_codes row or None."""
    subtotal = sum((line["qty"] * to_cents(line["unit_price"]) for line in lines), Decimal(0))
    food = sum((line["qty"] * to_cents(line["unit_price"]) for line in lines
                if line["category"] not in UNTAXED_CATEGORIES), Decimal(0))
    discount = Decimal(0)
    if promo is not None:
        if promo["percent_off"]:
            discount = to_cents(food * Decimal(str(promo["percent_off"])) / 100)
        elif promo["amount_off"]:
            discount = min(to_cents(promo["amount_off"]), food)
    tax = to_cents((food - discount) * TAX_RATE)
    total = subtotal - discount + tax
    return {name: float(value) for name, value in
            (("subtotal", subtotal), ("discount", discount), ("tax", tax), ("total", total))}
