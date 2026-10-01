# 2. Let customers choose a pickup time

Saturday mornings are chaos. Thirty people show up at 9am and the line goes out the door. I want customers to choose a pickup time when they order, and I want to cap how many orders we promise for each time.

- We're open Tuesday to Sunday, 7am to 3pm, and closed Mondays.
- Pickup times every half hour, starting at 7:00. The last one is 2:30.
- We can handle **4 orders per half hour**. When a time is full, people should pick another one.
- Everything needs at least **2 hours' notice**. Birthday cakes and catering trays need **2 days' notice**, because we bake them to order.
- If someone cancels, their time should open back up.
- On the orders page, show me each order's pickup time and put them in pickup order, so I can work down the list.

**Please don't lose the orders already in the system.** People have already ordered for next week; they just don't have a time yet.

> **Notes from Sam:**
>
> - Send the pickup time as `pickup_slot` in `"HH:MM"` 24-hour format, with the slot's start time (for example `"07:00"` or `"14:30"`). It's required for new orders, and orders include it in their JSON. Older orders with no time show `null`.
> - Times that aren't a half-hour slot, closed days and too-short notice are bad requests: `400` with an `error` message. A full slot is a conflict: `409` with an `error` message.
> - Notice is measured from now to the start of the slot: at least 2 hours, or at least 48 hours if the order has a Birthday Cake (CAKE48) or Catering Tray (CATER120).
> - Only orders that aren't cancelled count toward the 4.
> - Add `GET /api/slots?date=YYYY-MM-DD` for the checkout page. It returns `{"date": ..., "open": true/false, "slots": [{"time": "07:00", "remaining": 4, "available": true}, ...]}`. A closed day has `"open": false` and no slots. `available` means the slot still has room and is at least 2 hours away. A bad date is a `400`.
> - The checkout form needs a `<select name="pickup_slot">` that fills in for the chosen date.
> - `/admin/api/orders` and the admin page list orders by pickup date, then pickup time (orders without a time first), then order number.
