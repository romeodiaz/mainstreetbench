# 3. Stop selling more than we can bake

Last Saturday we sold nine birthday cakes. We can only make six a day, so I spent Friday night calling people to apologise. Some things we can only make so many of each day:

- Birthday cakes: **6 a day**
- Catering trays: **4 a day**
- Seasonal pies: **8 a day**

Everything else we can keep up with. I need to change these numbers myself when we're short-staffed or it's a holiday.

When we've sold out of something for a day, the menu should say **Sold out** for that day and nobody should be able to order it. If someone cancels, it should become available again. An order that would go over the limit shouldn't go through at all; I don't want half an order.

> **Notes from Sam:**
>
> - Each product gets a `daily_limit`: a whole number, or `null` for no limit. Both new and existing databases should start with the numbers above.
> - Limits are per pickup date. Count the quantity on every order for that date that isn't cancelled, including orders placed before this change.
> - Change a limit with `PUT /admin/api/products/<sku>` and `{"daily_limit": 5}` (or `null`). It's admin-only and returns the product with its `daily_limit`. A bad value is a `400`; an unknown SKU is a `404`.
> - `GET /api/menu?date=YYYY-MM-DD` adds `daily_limit`, `remaining` (`null` when there's no limit) and `sold_out` to each product. `GET /api/menu` without a date still includes `daily_limit`.
> - An order that asks for more than what's left is a `409` with `error`, the `sku` that ran out and how many are `remaining`. Count the same item on two lines together. Nothing from a rejected order is saved.
> - `/?date=YYYY-MM-DD` shows the menu for that pickup date. Sold-out items keep their `data-sku` row, add `data-sold-out="true"`, say "Sold out" and can't be added to the cart.
