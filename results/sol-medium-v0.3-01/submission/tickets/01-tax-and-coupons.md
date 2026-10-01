# 1. We're charging the wrong tax when people use a coupon

A customer emailed to say we charged her sales tax on the full price even though she used a coupon. My bookkeeper checked and she's right. Tax should be on what people actually pay for the food, after the coupon.

While she was looking, she found two more problems:

- **Gift cards are being taxed.** Gift cards aren't taxable; you pay tax when you spend them.
- **Coupons take money off gift cards.** If someone buys a $25 gift card with WELCOME10, they shouldn't get $2.50 off. Coupons are for food only.

She also says some totals are a penny off.

> **Notes from Sam** (he built the site and left these when I asked how it's supposed to work):
>
> - "Food" means everything except the Gift Cards category.
> - Percent coupons take that percent off the food subtotal. Dollar coupons take that amount off, but never more than the food subtotal.
> - Tax is 8% of (food subtotal − discount).
> - Round the discount and the tax to the cent, with half a cent always rounding up. That's how the bookkeeper does it.
> - `subtotal` stays the full subtotal, gift cards included. `total` = subtotal − discount + tax.
> - Keep the API fields as they are; the bookkeeper's export reads them.
