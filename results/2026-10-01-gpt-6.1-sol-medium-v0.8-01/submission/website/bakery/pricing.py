"""Order pricing. Coupons apply to food only, tax applies to food after the coupon, and gift cards are
never discounted or taxed. Cents round half up, as the bookkeeper does."""

from decimal import Decimal, ROUND_HALF_UP

UNTAXED_CATEGORIES = {"Gift Cards"}
NO_DISCOUNT_CATEGORIES = {"Gift Cards"}
CENT = Decimal("0.01")


def cents(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def price_order(lines: list, promo, rate: Decimal) -> dict:
    """lines: [{"qty", "unit_price", "category"}]; promo: a promo_codes row or None."""
    def total_of(keep) -> Decimal:
        return sum((line["qty"] * cents(line["unit_price"]) for line in lines if keep(line)), Decimal(0))

    subtotal = total_of(lambda line: True)
    discountable = total_of(lambda line: line["category"] not in NO_DISCOUNT_CATEGORIES)
    taxable = total_of(lambda line: line["category"] not in UNTAXED_CATEGORIES)
    discount = Decimal(0)
    if promo is not None:
        if promo["percent_off"]:
            discount = cents(discountable * Decimal(str(promo["percent_off"])) / 100)
        elif promo["amount_off"]:
            discount = min(cents(promo["amount_off"]), discountable)
    discount = min(discount, discountable)
    tax = cents(max(taxable - discount, Decimal(0)) * rate)
    total = subtotal - discount + tax
    return {name: float(value) for name, value in
            (("subtotal", subtotal), ("discount", discount), ("tax", tax), ("total", total))}
