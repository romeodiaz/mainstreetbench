"""Order pricing in decimal dollars, rounded like the bookkeeper's totals."""

from decimal import Decimal, ROUND_HALF_UP

TAX_RATE = Decimal('0.08')
CENT = Decimal('0.01')


def price_order(lines: list, promo) -> dict:
    def cents(value):
        return value.quantize(CENT, rounding=ROUND_HALF_UP)

    subtotal = cents(sum((Decimal(str(line['unit_price'])) * line['qty'] for line in lines), Decimal(0)))
    food = cents(sum((Decimal(str(line['unit_price'])) * line['qty'] for line in lines
                      if line.get('category') != 'Gift Cards'), Decimal(0)))
    discount = Decimal(0)
    if promo is not None:
        if promo['percent_off']:
            discount = cents(food * Decimal(str(promo['percent_off'])) / 100)
        elif promo['amount_off']:
            discount = cents(Decimal(str(promo['amount_off'])))
    discount = min(discount, food)
    tax = cents((food - discount) * TAX_RATE)
    return {key: float(value) for key, value in {
        'subtotal': subtotal, 'discount': discount, 'tax': tax,
        'total': cents(subtotal - discount + tax),
    }.items()}
