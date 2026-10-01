"""Prices use decimal arithmetic and round half cents up."""
from decimal import Decimal, ROUND_HALF_UP

TAX_RATE = Decimal('0.08')


def cents(value):
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def price_order(lines: list, promo) -> dict:
    subtotal = sum((cents(l['unit_price']) * l['qty'] for l in lines), Decimal(0))
    food = sum((cents(l['unit_price']) * l['qty'] for l in lines
                if l.get('category') != 'Gift Cards' and not l.get('sku', '').startswith('GIFT')), Decimal(0))
    discount = Decimal(0)
    if promo is not None:
        if promo['percent_off']:
            discount = cents(food * Decimal(str(promo['percent_off'])) / 100)
        elif promo['amount_off']:
            discount = cents(promo['amount_off'])
    discount = min(food, discount)
    tax = cents((food - discount) * TAX_RATE)
    return {k: float(v) for k, v in dict(subtotal=subtotal, discount=discount, tax=tax,
                                        total=subtotal - discount + tax).items()}
