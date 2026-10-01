#!/usr/bin/env python3
"""Reproducible, synthetic retail-reconciliation fixture for Main Street Bench.

The September packet is solver-visible. The answer keys are evaluator-only.
All expectations follow information supplied in the
packet; there are no corrections that require knowledge of hidden intent.

Python standard library only. By default writes beneath the repository root.
Use --output-root /tmp/retail-fixture-check to regenerate without changing it.
"""

from __future__ import annotations

import argparse
import calendar
import copy
import csv
import datetime as dt
import hashlib
import json
import random
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


DEFAULT_SEED = 20260930
VERSION = "0.1"
TASK_ID = "retail-reconciliation"
ORDER_COLUMNS = [
    "line_id", "order_id", "record_version", "ordered_at", "customer_id",
    "customer_name", "customer_email", "customer_phone", "sku", "product_name",
    "quantity", "unit_price", "discount_amount", "tax_amount", "line_total", "notes",
]
PAYMENT_COLUMNS = [
    "payment_id", "order_id", "payment_at", "tender", "status", "amount", "fee",
    "settled_at", "reference", "notes",
]
REFUND_COLUMNS = [
    "refund_id", "order_id", "line_id", "requested_at", "completed_at", "status",
    "quantity", "refund_sales", "refund_tax", "refund_total", "tender",
    "fee_adjustment", "settled_at", "notes",
]
CUSTOMER_COLUMNS = ["customer_id", "customer_name", "email", "phone", "loyalty_reference"]
PRODUCT_COLUMNS = ["sku", "product_name", "catalog_price", "category", "tax_rate"]
PRODUCTS = [
    {"sku": "BREAD9", "product_name": "Sourdough Loaf", "price": 900, "category": "merchandise"},
    {"sku": "CROISSANT21", "product_name": "Croissant Box (6)", "price": 2100, "category": "merchandise"},
    {"sku": "CAKE48", "product_name": "Birthday Cake", "price": 4800, "category": "merchandise"},
    {"sku": "COFFEE18", "product_name": "Coffee Beans 1lb", "price": 1800, "category": "merchandise"},
    {"sku": "CATER120", "product_name": "Catering Tray", "price": 12000, "category": "merchandise"},
    {"sku": "COOKIE12", "product_name": "Cookie Box (12)", "price": 1200, "category": "merchandise"},
    {"sku": "GIFT25", "product_name": "$25 Gift Card", "price": 2500, "category": "gift_card"},
]
BY_SKU = {p["sku"]: p for p in PRODUCTS}


def cents(value: object) -> int:
    return int((Decimal(str(value)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def money(value: int) -> str:
    return f"{value / 100:.2f}"


def dollars(value: int) -> float:
    return float(Decimal(value) / 100)


def rounded_ratio(value: int, numerator: int, denominator: int) -> int:
    return int((Decimal(value) * numerator / denominator).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def card_fee(amount: int) -> int:
    return rounded_ratio(amount, 29, 1000) + 30


def month_date(month: str, day: int) -> str:
    return f"{month}-{day:02d}"


def timestamp(date: str, hour: int = 12) -> str:
    # These are local store timestamps; no timezone conversion is required.
    return f"{date}T{hour:02d}:00:00"


def next_month(month: str) -> str:
    year, number = map(int, month.split("-"))
    return f"{year + (number == 12):04d}-{number % 12 + 1:02d}"


def previous_month(month: str) -> str:
    year, number = map(int, month.split("-"))
    return f"{year - (number == 1):04d}-{(number - 2) % 12 + 1:02d}"


def customers() -> list[dict[str, str]]:
    names = [
        "Maria Lopez", "James Chen", "Priya Patel", "Daniel Okafor", "Aisha Rahman",
        "Tom Walsh", "Keiko Tanaka", "Luis Garcia", "Grace Kim", "Omar Haddad",
        "Hannah Brooks", "Victor Nguyen", "Nina Petrov", "Alex Morgan", "Alex Morgan",
        "Ravi Iyer", "Elena Rossi", "Marcus Bell", "Sofia Costa", "Ben Fischer",
        "Fatima Ali", "Leo Moreau", "Ivy Reed", "Carlos Silva", "Megan Hughes",
        "Theo Park", "Zara Khan", "Noah Evans", "Lily Dubois", "Jonah Grant",
    ]
    result = []
    for number, name in enumerate(names, start=1):
        result.append({
            "customer_id": f"C{number:03d}", "customer_name": name,
            "email": name.lower().replace(" ", ".") + f"{number}@example.com",
            "phone": f"555-010-{number:04d}", "loyalty_reference": f"CL-{number:04d}",
        })
    for number in (14, 15):
        result[number - 1]["email"] = "morgan.household@example.com"
        result[number - 1]["phone"] = "555-010-1400"
    return result


def bookkeeping_notes(month: str) -> str:
    month_name = dt.date.fromisoformat(month + "-01").strftime("%B %Y")
    last_day = calendar.monthrange(*map(int, month.split("-")))[1]
    return f"""# Corner Loaf Bakery — bookkeeper's notes

Close month: {month}
Reporting period: {month}-01 through {month}-{last_day:02d}, inclusive.
All amounts are USD. All dates and times use our store's local calendar.
These are fictional training records, not real customers or financial data.

Please use these rules for our {month_name} close. The register and processor
exports cover the close month, plus older records needed to understand returns
and transactions that settle this month. An older order is supporting evidence,
not a new sale this month. Earlier-month card charges and completed refunds
settled in this month belong in expected payout, while their original sale,
payment, and refund-completion dates still control the other period totals.

## What each export means

- `orders.csv` is one row per order line, not one row per whole order. An order
  can have several products. `line_id` identifies a line across exports.
  Keep the highest `record_version` for each line; a newer version replaces the
  entire older line. Repeated identical rows are duplicate exports. Count the
  latest line once. Two different order IDs can be real repeat purchases even
  when everything else looks the same. All latest orders here were fulfilled.
- `payments.csv` includes register tenders and processor attempts. Count each
  `payment_id` once. `captured` means accepted; `declined` means no money was
  taken. A failed attempt followed by a captured payment is one accepted
  payment. Distinct captured IDs represent distinct actual tenders, including
  an accidental second charge; keep both and flag any excess. `reference` can
  contain `order:<order_id>` when the normal order field is missing. That exact
  reference is reliable. Do not guess a match from an amount or date alone.
- `refunds.csv` is the refund processor/register export. Count each `refund_id`
  once. Only `succeeded` refunds move money and reduce sales. `failed` and
  `pending` are requests that have not been paid. Each refund references one
  `line_id`; multiple lines on a receipt must not multiply the payment or refund.
  `refund_sales`, `refund_tax`, and `refund_total` are the actual approved amounts.
  A partial refund returns only the listed quantity and amounts. Do not refund
  the whole order just because one line has a refund. No succeeded refund in
  this packet is repeated as a payment row.
- `customers.csv` is our loyalty register. An explicit customer ID is
  authoritative even if a checkout name is abbreviated or contacts vary.
  Different IDs remain different people, including the two Alex Morgans who
  share household contact details. When an order has no ID, assign one only if
  its contact details or recorded loyalty reference identify exactly one
  register entry. If several entries fit, keep its sale and mark attribution
  `UNASSIGNED`; show that amount separately. Do not pick a person arbitrarily.
- `products.csv` supplies canonical names/categories by SKU and today's normal
  price. An order's recorded `unit_price` is the price actually agreed at sale;
  promotions may differ from the catalog. SKU is reliable even if the displayed
  product name varies. Do not overwrite a recorded price with today's catalog.

## Sales, discounts, tax, and gift cards

For merchandise, gross sales are quantity times the recorded unit price.
`discount_amount` is a total discount for that line, not a per-unit discount.
Sales before returns are gross less discount. Our training store charges 8%
tax on discounted merchandise, rounded to cents per line using half-up rounding.
`tax_amount` is the recorded tax and `line_total` is discounted sales plus tax.
All latest line arithmetic in these exports is consistent with these rules.
Use integer cents or decimal arithmetic. Do not round only after aggregating.

Recognize fulfilled sales on `ordered_at`. Recognize a succeeded return on
`completed_at`, even when its original sale happened in an earlier month.
For this close, net sales = this month's merchandise sales after discounts
minus merchandise `refund_sales` completed this month. Net units by product
follow the same timing rule. Product and customer sales rankings use this
net-sales definition and exclude sales tax and gift-card issuance. Show both
net units and net sales for best-selling products; rank the sales table by
net sales, so the ranking has a clear meaning. Show unassigned customer sales
separately from the ranked list of known customers.

Gift-card SKU GIFT25 is stored value: selling it raises money and a gift-card
liability but creates no earned sales and no tax. Redeeming an existing gift
card is payment toward merchandise, which earns sales normally. We have no
gift-card refunds in these files. Show issuance and redemption separately;
the period's liability change is issuance minus redemption. You cannot work
out the total outstanding liability without the opening balance, which is
not supplied. A quantity of two gift cards is $50 of issuance.

Each order's amount due is the sum of its latest `line_total`, including tax
and any gift-card purchase. Compare that amount with all captured tenders for
the order, before refunds. A succeeded refund does not make a paid order
unpaid. Show positive shortfalls as unpaid balances and excess captured
amounts as overpayments. Keep unmatched accepted payments in processor cash
totals while flagging them; they are not evidence of another earned sale.

## Money received and expected payout

Show captured card, cash, and redeemed gift-card tender separately using
`payment_at` in the close month. Show succeeded card and cash refunds separately
using `completed_at`. Gift-card redemption brings no new external money.
Net external receipts = captured card plus cash minus succeeded card plus
cash refunds completed in the month. Cash after refunds = captured cash less
succeeded cash refunds. These are receipt movements, not earned sales.

The recorded `fee` is authoritative. This processor charges 2.9% plus $0.30
for each accepted card charge, rounded half-up to cents; declined attempts
and cash/gift-card tenders have zero fees. Refund fees are not automatically
returned. A positive `fee_adjustment` is an explicitly credited fee; use only
what the refund export says. Show card-processing fees for charges accepted
this month. Net receipts after fees subtracts those fees from net external
receipts and adds fee adjustments on returns completed this month.

Expected card payout for the close month follows `settled_at`, which can differ
from sale or payment dates: sum accepted card amounts settled this month,
subtract succeeded card refunds settled this month, subtract the fees attached
to those settled charges, and add fee adjustments attached to those settled
refunds. Include real second charges and unmatched processor charges in this
cash calculation and flag them separately. Show accepted card charges and
completed card refunds that will settle in a later month separately.

There is no bank statement here. This is expected processor payout, not
confirmation of a deposit or reconciliation to the bank. Do not add cash or
gift-card redemption to the expected card payout.

## Review

Keep the source files unchanged. Give us traceable order/payment/refund IDs
for anything needing follow-up, and explain what evidence is missing. An
unassigned customer still counts in store/product totals. A payment mismatch
does not invalidate a supported fulfilled sale. Please show each real order
once in customer order counts; a line, payment attempt, and refund are not
additional orders. Only orders placed in the close month count, so a prior
month's customer can have a refund deduction with zero orders this month.

Sort rankings by net sales descending; ties can be displayed together or by ID
for a stable display.
"""


def build_packet(month: str, seed: int, count: int) -> dict:
    rng = random.Random(seed)
    clients = customers()
    by_customer = {c["customer_id"]: c for c in clients}
    prefix = month.replace("-", "")
    prior = previous_month(month)
    future = next_month(month)
    last_day = calendar.monthrange(*map(int, month.split("-")))[1]
    orders: list[dict] = []
    payments: list[dict] = []
    refunds: list[dict] = []
    cases: list[dict] = []
    serial = 0

    def oid(number: int) -> str:
        return f"O-{prefix}-{number:03d}"

    def add_order(number: int, client: str, day: int, specs: list[tuple], *,
                  date: str | None = None, missing_id: bool = False,
                  alias: str = "", notes: str = "") -> list[dict]:
        customer = by_customer[client]
        rows = []
        for index, spec in enumerate(specs, start=1):
            sku, quantity = spec[:2]
            discount = spec[2] if len(spec) > 2 else 0
            price = spec[3] if len(spec) > 3 else BY_SKU[sku]["price"]
            net = price * quantity - discount
            tax = rounded_ratio(net, 8, 100) if BY_SKU[sku]["category"] == "merchandise" else 0
            row = {
                "line_id": f"{oid(number)}-L{index:02d}", "order_id": oid(number),
                "record_version": "1", "ordered_at": timestamp(date or month_date(month, day)),
                "customer_id": "" if missing_id else client,
                "customer_name": alias or customer["customer_name"],
                "customer_email": customer["email"], "customer_phone": customer["phone"],
                "sku": sku, "product_name": BY_SKU[sku]["product_name"],
                "quantity": str(quantity), "unit_price": money(price),
                "discount_amount": money(discount), "tax_amount": money(tax),
                "line_total": money(net + tax), "notes": notes,
            }
            orders.append(row)
            rows.append(row)
        return rows

    def add_payment(number: int | None, amount: int, date: str, *, tender: str = "card",
                    status: str = "captured", settled: str | None = None,
                    reference: str = "", notes: str = "", exported_order: bool = True) -> dict:
        nonlocal serial
        serial += 1
        payment = {
            "payment_id": f"P-{prefix}-{serial:03d}",
            "order_id": oid(number) if number is not None and exported_order else "",
            "payment_at": timestamp(date, 13), "tender": tender, "status": status,
            "amount": money(amount),
            "fee": money(card_fee(amount) if tender == "card" and status == "captured" else 0),
            "settled_at": (settled or date) if status == "captured" else "",
            "reference": reference or (f"order:{oid(number)}" if number is not None else ""),
            "notes": notes,
        }
        payments.append(payment)
        return payment

    def due(rows: list[dict]) -> int:
        return sum(cents(r["line_total"]) for r in rows)

    def add_refund(number: int, row: dict, quantity: int, day: int, *, status: str = "succeeded",
                   tender: str = "card", settled: str | None = None, adjustment: int = 0) -> dict:
        qty = int(row["quantity"])
        sales = cents(row["unit_price"]) * qty - cents(row["discount_amount"])
        refund_sales = rounded_ratio(sales, quantity, qty)
        refund_tax = rounded_ratio(cents(row["tax_amount"]), quantity, qty)
        completed = timestamp(month_date(month, day), 16) if status == "succeeded" else ""
        refund = {
            "refund_id": f"R-{prefix}-{number:03d}", "order_id": row["order_id"],
            "line_id": row["line_id"], "requested_at": timestamp(month_date(month, day), 15),
            "completed_at": completed, "status": status, "quantity": str(quantity),
            "refund_sales": money(refund_sales), "refund_tax": money(refund_tax),
            "refund_total": money(refund_sales + refund_tax), "tender": tender,
            "fee_adjustment": money(adjustment),
            "settled_at": (settled or month_date(month, day)) if status == "succeeded" else "",
            "notes": "Partial item return" if quantity < qty else "Item return",
        }
        refunds.append(refund)
        return refund

    def case(id_: str, title: str, kind: str, records: list[str], behavior: str,
             amount: int | None = None) -> None:
        entry = {"id": id_, "title": title, "kind": kind, "record_ids": records,
                 "expected_behavior": behavior}
        if amount is not None:
            entry["expected_amount"] = dollars(amount)
        cases.append(entry)

    # Fixed cases are intentionally ordinary business events with interactions.
    amended = add_order(1, "C001", 2, [("BREAD9", 2), ("CROISSANT21", 1)])
    amended[0]["record_version"] = "2"
    add_payment(1, due(amended), month_date(month, 2))
    case("latest-line-version", "Amended order line", "resolve", [amended[0]["line_id"]],
         "Use version 2 (two loaves) once; discard version 1, which has one loaf.")

    repeat_ids = []
    for number, day in ((2, 4), (3, 5)):
        rows = add_order(number, "C002", day, [("COFFEE18", 1), ("BREAD9", 1)])
        add_payment(number, due(rows), month_date(month, day))
        repeat_ids.append(oid(number))
    case("legitimate-repeat", "Similar repeat purchases", "preserve", repeat_ids,
         "Retain both order IDs, each with its own captured payment; these are two real purchases.")

    rows = add_order(4, "C004", 6, [("CAKE48", 1), ("COOKIE12", 2)])
    declined = add_payment(4, due(rows), month_date(month, 6), status="declined")
    accepted = add_payment(4, due(rows), month_date(month, 6))
    case("failed-authorization", "Declined attempt followed by payment", "resolve",
         [oid(4), declined["payment_id"], accepted["payment_id"]],
         "Count the captured payment and its fee once; do not count the declined attempt as receipts or an overpayment.")

    rows = add_order(5, "C005", 7, [("CAKE48", 1), ("COFFEE18", 1)])
    gift = add_payment(5, 2500, month_date(month, 7), tender="gift_card")
    card = add_payment(5, due(rows) - 2500, month_date(month, 7))
    case("split-tender", "Gift-card and card split tender", "resolve",
         [oid(5), gift["payment_id"], card["payment_id"]],
         "Keep merchandise sales of $66.00; the $25.00 gift-card redemption is a tender, not additional external receipts or sales.", 2500)

    rows = add_order(6, "C006", 8, [("GIFT25", 2)])
    add_payment(6, due(rows), month_date(month, 8))
    case("gift-card-issuance", "Selling stored value", "resolve", [oid(6)],
         "Record $50.00 as gift-card issuance and accepted card receipts, with zero earned sales and zero tax.", 5000)

    rows = add_order(7, "C007", 9, [("CATER120", 1), ("BREAD9", 1)])
    first = add_payment(7, due(rows), month_date(month, 9))
    second = add_payment(7, due(rows), month_date(month, 9), notes="Second accepted terminal charge")
    case("actual-double-charge", "Two actual captured transactions", "review",
         [oid(7), first["payment_id"], second["payment_id"]],
         "Retain both distinct captured payment IDs in cash and payout totals, count the sale once, and flag the $139.32 excess charge. Do not silently delete or refund it.", due(rows))

    rows = add_order(8, "C008", 10, [("BREAD9", 3), ("COFFEE18", 1)])
    case("missing-payment", "Fulfilled order without a payment", "review", [oid(8)],
         "Keep $45.00 earned sales and flag the $48.60 amount due as unsupported by a captured tender. Do not invent a payment or remove the sale.", due(rows))

    rows = add_order(9, "C009", 11, [("CROISSANT21", 3, 630), ("CAKE48", 1)])
    add_payment(9, due(rows), month_date(month, 11))
    partial = add_refund(1, rows[0], 1, 14, adjustment=30)
    case("partial-refund", "Discounted partial line return", "resolve",
         [oid(9), rows[0]["line_id"], partial["refund_id"]],
         "Deduct one croissant box, $18.90 sales and $1.51 tax; the other two boxes and cake remain sold. The $0.30 fee adjustment is an explicit processor credit.", 2041)

    rows = add_order(10, "C010", 12, [("BREAD9", 2), ("CAKE48", 1)])
    add_payment(10, due(rows), month_date(month, 12))
    failed = add_refund(2, rows[0], 1, 14, status="failed")
    pending = add_refund(3, rows[1], 1, 15, status="pending")
    case("unpaid-refund-requests", "Failed and pending returns", "review",
         [oid(10), failed["refund_id"], pending["refund_id"]],
         "Flag the failed $9.72 and pending $51.84 refund requests for follow-up; neither changes units, sales, receipts, or payout until succeeded.", 6156)

    rows = add_order(11, "C011", last_day, [("COFFEE18", 2), ("BREAD9", 2)])
    later = add_payment(11, due(rows), month_date(month, last_day), settled=month_date(future, 2))
    case("settlement-cutoff", "Month-end charge settles next month", "resolve",
         [oid(11), later["payment_id"]],
         f"Count $54.00 sales and $58.32 accepted card receipts in {month}, but exclude this charge and its $1.99 fee from that month's payout; settlement is {future}-02.", due(rows))

    for number, client, specs in (
        (12, "C014", [("BREAD9", 2), ("COOKIE12", 1)]),
        (13, "C015", [("COFFEE18", 2), ("CROISSANT21", 1)]),
    ):
        rows = add_order(number, client, 16, specs)
        add_payment(number, due(rows), month_date(month, 16))
    case("shared-household", "Two people share a name and contacts", "preserve",
         ["C014", "C015", oid(12), oid(13)],
         "Preserve C014 and C015 as separate customers despite identical Alex Morgan name/email/phone; explicit customer IDs determine attribution.")

    rows = add_order(14, "C003", 17, [("CAKE48", 1), ("COOKIE12", 1)],
                     missing_id=True, alias="P. Patel", notes="Loyalty receipt CL-0003 shown at pickup")
    add_payment(14, due(rows), month_date(month, 17))
    case("supported-customer-link", "Recoverable missing loyalty ID", "resolve", [oid(14), "C003"],
         "Assign C003 using the unique customer email and the matching CL-0003 loyalty reference; normalize its display name without creating an extra customer.")

    rows = add_order(15, "C014", 18, [("CROISSANT21", 1), ("COOKIE12", 1)],
                     missing_id=True, notes="Pickup name Alex; no loyalty reference supplied")
    add_payment(15, due(rows), month_date(month, 18))
    case("ambiguous-customer", "Missing ID with shared household contacts", "review",
         [oid(15), "C014", "C015"],
         "Keep $33.00 in store and product net sales but attribute it to UNASSIGNED; flag that C014 versus C015 cannot be established from these files.", 3300)

    rows = add_order(16, "C001", 19, [("BREAD9", 3), ("COFFEE18", 1)], alias="Lopez, Maria")
    rows[0]["product_name"] = "sourdough loaf"
    add_payment(16, due(rows), month_date(month, 19))
    case("stable-identity", "Checkout and product label variants", "resolve", [oid(16), "C001", "BREAD9"],
         "Use C001 and BREAD9 for aggregation despite display label variants; do not create duplicate customer or product categories.")

    rows = add_order(17, "C017", 20, [("COOKIE12", 3), ("BREAD9", 2)])
    add_payment(17, due(rows), month_date(month, 20), tender="cash")
    cash_return = add_refund(4, rows[0], 1, 22, tender="cash")
    case("cash-return", "Cash purchase and item refund", "resolve",
         [oid(17), cash_return["refund_id"]],
         "Include the $12.96 cash refund in cash-after-refunds and the $12.00 sales reduction; exclude all cash from card payout.", 1296)

    rows = add_order(18, "C018", 21, [("COFFEE18", 2, 0, 1650), ("CROISSANT21", 1, 210)])
    add_payment(18, due(rows), month_date(month, 21))
    case("recorded-promotion", "Recorded promotional price and discount", "preserve", [oid(18)],
         "Keep the recorded $16.50 coffee price instead of replacing it with the $18.00 catalog price, and apply the $2.10 croissant line discount once.")

    rows = add_order(19, "C019", 22, [("CAKE48", 1), ("BREAD9", 2)])
    referenced = add_payment(19, due(rows), month_date(month, 22), exported_order=False)
    case("payment-reference", "Payment missing the usual order field", "resolve",
         [oid(19), referenced["payment_id"]],
         "Recover the exact order link from reference order:<order_id>; this payment is supported, not unmatched.")

    rows = add_order(20, "C020", 23, [("COFFEE18", 2), ("COOKIE12", 2)])
    add_payment(20, due(rows), month_date(month, 23))
    later_refund = add_refund(5, rows[0], 1, last_day, settled=month_date(future, 2))
    case("refund-settlement-cutoff", "Completed return settles next month", "resolve",
         [oid(20), later_refund["refund_id"]],
         f"Deduct $18.00 sales and $19.44 card refund receipts in {month}; exclude this refund from that month's payout because settlement is {future}-02.", 1944)

    # Supporting prior-month order is in the exported packet, with its payment.
    prior_rows = add_order(0, "C005", 10, [("CAKE48", 1, 480), ("CROISSANT21", 2)],
                           date=month_date(prior, 26), notes="Prior-month receipt retained for return support")
    add_payment(0, due(prior_rows), month_date(prior, 26))
    old_return = add_refund(6, prior_rows[0], 1, 8)
    case("prior-month-return", "Return from a prior month's sale", "resolve",
         [oid(0), old_return["refund_id"]],
         f"Exclude the original {prior} order and charge from {month} sales/receipts, but deduct the succeeded $43.20 sales/$3.46 tax return completed and settled in {month}.", 4666)

    unmatched = add_payment(None, 3780, month_date(month, 24), reference="terminal:unlinked-884",
                            notes="Processor export has no order reference")
    case("unmatched-processor-charge", "Accepted processor charge without an order", "review",
         [unmatched["payment_id"]],
         "Include the real $37.80 accepted charge and its $1.40 fee in processor receipt/payout totals; flag the missing order evidence without inventing earned sales.", 3780)

    merchandise_skus = [p["sku"] for p in PRODUCTS if p["category"] == "merchandise"]
    for number in range(21, count + 1):
        client = rng.choices(clients, weights=[6, 5, 4] + [1] * 27)[0]["customer_id"]
        day = rng.randint(1, max(1, last_day - 3))
        line_count = rng.choices([1, 2, 3], weights=[1, 7, 2])[0]
        selected = rng.sample(merchandise_skus, line_count)
        if number % 19 == 0:
            selected[-1] = "GIFT25"
        specs = []
        for sku in selected:
            quantity = 1 if sku in {"CAKE48", "CATER120"} else rng.randint(1, 3)
            gross = BY_SKU[sku]["price"] * quantity
            percentage = rng.choice([0, 0, 0, 5, 10]) if sku != "GIFT25" else 0
            specs.append((sku, quantity, rounded_ratio(gross, percentage, 100)))
        rows = add_order(number, client, day, specs)
        if number % 17 == 0 and all(r["sku"] != "GIFT25" for r in rows):
            redeem = min(2500, due(rows))
            add_payment(number, redeem, month_date(month, day), tender="gift_card")
            if due(rows) > redeem:
                add_payment(number, due(rows) - redeem, month_date(month, day))
        else:
            tender = "cash" if number % 7 == 0 else "card"
            add_payment(number, due(rows), month_date(month, day), tender=tender)

    # Save an internal ledger of canonical, source-supported records. Expected
    # figures come from this ledger, never from a model's output.
    ledger = {"orders": copy.deepcopy(orders), "payments": copy.deepcopy(payments),
              "refunds": copy.deepcopy(refunds), "customers": clients, "month": month}
    older = copy.deepcopy(amended[0])
    older.update(record_version="1", quantity="1", tax_amount="0.72", line_total="9.72")
    older["notes"] = "Original line before amendment"
    orders.append(older)
    duplicate_lines = [orders[index] for index in (3, 17, 28, len(orders) - 4)]
    orders.extend(copy.deepcopy(duplicate_lines))
    duplicate_payments = [payments[index] for index in (2, 9, 18)]
    payments.extend(copy.deepcopy(duplicate_payments))
    refunds.append(copy.deepcopy(partial))
    case("duplicate-exports", "Repeated exports across all transaction files", "resolve",
         [r["line_id"] for r in duplicate_lines] + [p["payment_id"] for p in duplicate_payments] + [partial["refund_id"]],
         "Count repeated same-ID rows once in orders, payments, and refunds. Do not confuse repeated exports with distinct captured charges or real repeat order IDs.")
    rng.shuffle(orders)
    rng.shuffle(payments)
    rng.shuffle(refunds)
    return {"orders": orders, "payments": payments, "refunds": refunds, "customers": clients,
            "ledger": ledger, "month": month, "cases": cases, "notes": bookkeeping_notes(month)}


def expected(ledger: dict) -> dict:
    """Account from the canonical ledger using the explicitly supplied rules."""
    month = ledger["month"]
    period_lines = [r for r in ledger["orders"] if r["ordered_at"].startswith(month)]
    by_line = {r["line_id"]: r for r in ledger["orders"]}
    active_refunds = [r for r in ledger["refunds"] if r["status"] == "succeeded"
                      and r["completed_at"].startswith(month)]
    accepted = [p for p in ledger["payments"] if p["status"] == "captured"
                and p["payment_at"].startswith(month)]
    order_totals = defaultdict(int)
    customer_orders = defaultdict(set)
    product_units = defaultdict(int)
    product_sales = defaultdict(int)
    customer_sales = defaultdict(int)
    customer_by_id = {c["customer_id"]: c for c in ledger["customers"]}

    def client(row: dict) -> str:
        if row["customer_id"]:
            return row["customer_id"]
        matching = [c for c in ledger["customers"] if c["email"] == row["customer_email"]]
        if len(matching) == 1:
            return matching[0]["customer_id"]
        references = [c for c in ledger["customers"] if c["loyalty_reference"] in row["notes"]]
        return references[0]["customer_id"] if len(references) == 1 else "UNASSIGNED"

    gross = discounts = tax = gift_issued = 0
    for row in period_lines:
        quantity = int(row["quantity"])
        order_totals[row["order_id"]] += cents(row["line_total"])
        customer_orders[client(row)].add(row["order_id"])
        if BY_SKU[row["sku"]]["category"] == "gift_card":
            gift_issued += quantity * cents(row["unit_price"])
            continue
        sales = quantity * cents(row["unit_price"]) - cents(row["discount_amount"])
        gross += quantity * cents(row["unit_price"])
        discounts += cents(row["discount_amount"])
        tax += cents(row["tax_amount"])
        product_units[row["sku"]] += quantity
        product_sales[row["sku"]] += sales
        customer_sales[client(row)] += sales
    for refund in active_refunds:
        source = by_line[refund["line_id"]]
        product_units[source["sku"]] -= int(refund["quantity"])
        product_sales[source["sku"]] -= cents(refund["refund_sales"])
        customer_sales[client(source)] -= cents(refund["refund_sales"])

    order_tenders = defaultdict(int)
    unmatched = 0
    for payment in ledger["payments"]:
        if payment["status"] != "captured":
            continue
        order_id = payment["order_id"]
        if not order_id and payment["reference"].startswith("order:"):
            order_id = payment["reference"].split(":", 1)[1]
        if order_id in order_totals:
            order_tenders[order_id] += cents(payment["amount"])
        elif not order_id and payment in accepted and payment["tender"] == "card":
            unmatched += cents(payment["amount"])
    unpaid = sum(max(amount - order_tenders[order_id], 0) for order_id, amount in order_totals.items())
    overpaid = sum(max(order_tenders[order_id] - amount, 0) for order_id, amount in order_totals.items())
    captured = {t: sum(cents(p["amount"]) for p in accepted if p["tender"] == t)
                for t in ("card", "cash", "gift_card")}
    returned = {t: sum(cents(r["refund_total"]) for r in active_refunds if r["tender"] == t)
                for t in ("card", "cash")}
    fees = sum(cents(p["fee"]) for p in accepted if p["tender"] == "card")
    adjustments = sum(cents(r["fee_adjustment"]) for r in active_refunds)
    settled_charges = [p for p in ledger["payments"] if p["status"] == "captured"
                       and p["tender"] == "card" and p["settled_at"].startswith(month)]
    settled_returns = [r for r in ledger["refunds"] if r["status"] == "succeeded"
                       and r["tender"] == "card" and r["settled_at"].startswith(month)]
    payout = (sum(cents(p["amount"]) - cents(p["fee"]) for p in settled_charges)
              - sum(cents(r["refund_total"]) - cents(r["fee_adjustment"]) for r in settled_returns))
    refund_sales = sum(cents(r["refund_sales"]) for r in active_refunds)
    refund_tax = sum(cents(r["refund_tax"]) for r in active_refunds)
    external = captured["card"] + captured["cash"] - sum(returned.values())
    values = {
        "merchandise_gross_sales": gross, "discounts": discounts,
        "merchandise_sales_before_refunds": gross - discounts,
        "successful_refund_sales": refund_sales, "net_sales": gross - discounts - refund_sales,
        "sales_tax_charged": tax, "successful_refund_tax": refund_tax, "net_sales_tax": tax - refund_tax,
        "gift_card_issued": gift_issued, "gift_card_redeemed": captured["gift_card"],
        "gift_card_liability_change": gift_issued - captured["gift_card"],
        "customer_amount_due": sum(order_totals.values()),
        "captured_card_payments": captured["card"], "captured_cash_payments": captured["cash"],
        "captured_gift_card_payments": captured["gift_card"], "total_captured_payments": sum(captured.values()),
        "successful_card_refunds": returned["card"], "successful_cash_refunds": returned["cash"],
        "total_successful_refunds": sum(returned.values()), "card_processing_fees": fees,
        "refund_fee_adjustments": adjustments, "expected_card_payout": payout,
        "card_captures_settling_later": sum(cents(p["amount"]) for p in accepted
                                             if p["tender"] == "card" and p["settled_at"][:7] > month),
        "card_refunds_settling_later": sum(cents(r["refund_total"]) for r in active_refunds
                                            if r["tender"] == "card" and r["settled_at"][:7] > month),
        "unpaid_order_balance": unpaid, "overpaid_order_balance": overpaid,
        "unmatched_card_payments": unmatched, "unassigned_customer_net_sales": customer_sales["UNASSIGNED"],
        "cash_after_refunds": captured["cash"] - returned["cash"],
        "net_external_receipts": external, "net_receipts_after_fees": external - fees + adjustments,
    }
    metrics = {name: dollars(value) for name, value in values.items()}
    metrics["order_count"] = len(order_totals)
    product_rows = [{"sku": p["sku"], "product_name": p["product_name"],
                     "net_units": product_units[p["sku"]], "net_sales": dollars(product_sales[p["sku"]])}
                    for p in PRODUCTS if p["category"] == "merchandise"]
    product_rows.sort(key=lambda r: (-r["net_sales"], r["sku"]))
    # Include inactive loyalty records too: keeping a legitimate roster row
    # must never look like a false merge or an invented sale to a reviewer.
    customer_ids = set(customer_by_id) | set(customer_orders) | set(customer_sales)
    customer_rows = [{"customer_id": cid, "customer_name": customer_by_id.get(cid, {}).get("customer_name", "Unassigned customer"),
                      "order_count": len(customer_orders[cid]), "net_sales": dollars(customer_sales[cid])}
                     for cid in customer_ids]
    customer_rows.sort(key=lambda r: (-r["net_sales"], r["customer_id"]))
    known_customer_rows = [row for row in customer_rows if row["customer_id"] != "UNASSIGNED"]
    return {"metrics": metrics, "products": product_rows, "customers": customer_rows,
            "top_customers": copy.deepcopy(known_customer_rows[:10])}


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_packet(path: Path, packet: dict) -> dict[str, str]:
    path.mkdir(parents=True, exist_ok=True)
    for name, columns in (("orders", ORDER_COLUMNS), ("payments", PAYMENT_COLUMNS),
                          ("refunds", REFUND_COLUMNS), ("customers", CUSTOMER_COLUMNS)):
        write_csv(path / f"{name}.csv", packet[name], columns)
    catalog = [{"sku": p["sku"], "product_name": p["product_name"], "catalog_price": money(p["price"]),
                "category": p["category"], "tax_rate": "0.08" if p["category"] == "merchandise" else "0.00"}
               for p in PRODUCTS]
    write_csv(path / "products.csv", catalog, PRODUCT_COLUMNS)
    (path / "bookkeeping_notes.md").write_text(packet["notes"], encoding="utf-8")
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.iterdir()) if p.is_file() and p.name in {
                "orders.csv", "payments.csv", "refunds.csv", "customers.csv", "products.csv", "bookkeeping_notes.md"}}


def verify_packet(packet: dict) -> None:
    """Check exported keys/arithmetic and independently reconstruct canonical rows."""
    latest = {}
    for row in packet["orders"]:
        known = latest.get(row["line_id"])
        if known is None or int(row["record_version"]) > int(known["record_version"]):
            latest[row["line_id"]] = row
        elif row["record_version"] == known["record_version"]:
            assert row == known, f"Conflicting same-version export {row['line_id']}"
    canonical_orders = sorted(packet["ledger"]["orders"], key=lambda r: r["line_id"])
    assert sorted(latest.values(), key=lambda r: r["line_id"]) == canonical_orders
    for row in latest.values():
        subtotal = int(row["quantity"]) * cents(row["unit_price"]) - cents(row["discount_amount"])
        category = BY_SKU[row["sku"]]["category"]
        assert cents(row["tax_amount"]) == (rounded_ratio(subtotal, 8, 100) if category == "merchandise" else 0)
        assert cents(row["line_total"]) == subtotal + cents(row["tax_amount"])
    for collection, key in (("payments", "payment_id"), ("refunds", "refund_id")):
        deduped = {}
        for row in packet[collection]:
            assert row[key] not in deduped or row == deduped[row[key]], f"Conflicting {key}"
            deduped[row[key]] = row
        assert sorted(deduped.values(), key=lambda r: r[key]) == sorted(packet["ledger"][collection], key=lambda r: r[key])
    for refund in packet["refunds"]:
        assert refund["line_id"] in latest
        assert refund["order_id"] == latest[refund["line_id"]]["order_id"]
        assert cents(refund["refund_total"]) == cents(refund["refund_sales"]) + cents(refund["refund_tax"])
    answer = expected(packet["ledger"])
    m = {k: cents(v) for k, v in answer["metrics"].items() if k != "order_count"}
    assert sum(cents(p["net_sales"]) for p in answer["products"]) == m["net_sales"]
    assert sum(cents(c["net_sales"]) for c in answer["customers"]) == m["net_sales"]
    assert sum(c["order_count"] for c in answer["customers"]) == answer["metrics"]["order_count"]
    assert m["total_captured_payments"] - m["customer_amount_due"] == m["overpaid_order_balance"] - m["unpaid_order_balance"] + m["unmatched_card_payments"]
    assert m["unpaid_order_balance"] == 4860 and m["overpaid_order_balance"] == 13932
    assert m["unassigned_customer_net_sales"] == 3300
    assert m["card_captures_settling_later"] == 5832 and m["card_refunds_settling_later"] == 1944


def markdown_key(key: dict, initial: dict) -> str:
    lines = [
        "# Retail reconciliation — evaluator answer key", "",
        f"Task: {TASK_ID}; version {VERSION}; fixture seed {key['fixture_seed']}.", "",
        "Keep this key and the generator out of the solver workspace.",
        "The task is newly authored and has not been run or calibrated against any model.", "",
        "The JSON beside this file supplies exact cents-rounded expectations and SHA-256 input manifests.",
        "Expectations are derived from the source-supported canonical ledger; no model produced these answers.", "",
        "## Scope and calculations", "",
        f"Close: {initial['month']}; {key['metrics']['order_count']} real current-month orders. "
        f"Orders export: {len(initial['orders'])} rows for {len(initial['ledger']['orders'])} canonical lines "
        "(including two prior-month supporting lines).", "",
        "The bookkeeper notes are the authority for period, rounding, source keys, sales/tender treatment, and settlement timing. "
        "Use the latest order-line version, unique payment/refund IDs, and only succeeded refunds. "
        "The SKU catalog identifies category and canonical display name; recorded unit prices remain authoritative.", "",
        "Gross merchandise sales − line discounts − succeeded merchandise refunds completed in the close month = net sales. "
        "Sales tax and gift-card issuance are separate. Net units subtract only completed succeeded refund quantities. "
        "The prior-month sale is excluded; its current-month return is included.", "",
        "Customer order counts count distinct fulfilled current-month order IDs, including a gift-card-only order. "
        "Customer net sales exclude gift-card issuance and tax and include current-month refund deductions. "
        "Missing-ID orders are matched only on unique evidence; the shared Alex Morgan household order stays UNASSIGNED. "
        "The unassigned bucket is included in the customer table so totals reconcile. "
        "Every legitimate loyalty-register customer is included, with zero orders and zero net sales when inactive; "
        "retaining an inactive roster entry is correct.", "",
        "Compare original order amount due with captured tenders before returns. "
        "A refund does not reopen the customer's original amount due. "
        "Keep distinct actual charges in processor receipts, even when an order is overpaid. "
        "An unmatched processor charge affects cash/payout but never creates an unsupported sale.", "",
        "Expected card payout uses settled_at: captured card amount less its fee, minus succeeded settled card refunds, "
        "plus their explicit fee adjustments. Cash, gift-card tenders, and unsettled transactions are excluded. "
        "There is no bank statement, opening gift-card balance, or evidence authorizing automatic refunds.", "",
        "## Metrics", "", "| Metric | Expected |", "| --- | ---: |",
    ]
    for name, value in key["metrics"].items():
        shown = str(value) if name == "order_count" else f"${value:,.2f}"
        lines.append(f"| `{name}` | {shown} |")
    lines += ["", "## Products", "", "Gift-card issuance is excluded from this earned-sales ranking.", "",
              "| SKU | Net units | Net sales |", "| --- | ---: | ---: |"]
    lines += [f"| {p['sku']} | {p['net_units']} | ${p['net_sales']:,.2f} |" for p in key["products"]]
    lines += ["", "## Top customers", "", "| Rank | Customer ID | Name | Orders | Net sales |", "| --- | --- | --- | ---: | ---: |"]
    lines += [f"| {i} | {c['customer_id']} | {c['customer_name']} | {c['order_count']} | ${c['net_sales']:,.2f} |"
              for i, c in enumerate(key["top_customers"], start=1)]
    lines += ["", "All customer rows, including the unassigned bucket, are in the JSON. Equal-value ties can be displayed in either order.",
              "", "## Evidence-backed cases", "",
              "A `resolve` case has sufficient evidence for a specific answer; merely flagging it does not demonstrate resolution. "
              "A `review` case must remain visible with the supported amount and record IDs. "
              "A `preserve` case checks that the solver retains valid records or prices instead of manufacturing a correction.", ""]
    for case in key["cases"]:
        lines += [f"### {case['id']} — {case['title']} ({case['kind']})", "",
                  "Records: " + ", ".join(f"`{record}`" for record in case["record_ids"]) + ".", "",
                  case["expected_behavior"], ""]
    lines += ["## Fixture integrity", "",
              "The generator checks latest versions, exact duplicate IDs, all line and refund arithmetic, cross-file references, "
              "product/customer totals, distinct customer order counts, open/overpaid balances, and the tender-to-order reconciliation bridge. "
              "Default-seed regeneration must be byte-for-byte deterministic, including answer keys. "
              f"Use `python3 tasks/{TASK_ID}/generate.py --output-root /tmp/retail-fixture-check` to regenerate elsewhere.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.output_root.resolve()
    task_dir = root / "tasks" / TASK_ID
    initial = build_packet("2026-09", args.seed, 100)
    verify_packet(initial)
    initial_hashes = write_packet(task_dir / "inputs", initial)
    key = {"task_id": TASK_ID, "version": VERSION, "fixture_seed": args.seed, "currency": "USD",
           "reporting_period": "2026-09", "status": "authored_not_calibrated", "input_hashes": initial_hashes,
           **expected(initial["ledger"]), "cases": initial["cases"]}
    key_dir = root / "answer-keys"
    key_dir.mkdir(parents=True, exist_ok=True)
    (key_dir / f"{TASK_ID}.json").write_text(json.dumps(key, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (key_dir / f"{TASK_ID}.md").write_text(markdown_key(key, initial), encoding="utf-8")
    print(f"Generated {TASK_ID} v{VERSION} at {root}")
    result = expected(initial["ledger"])
    print(f"September: {result['metrics']['order_count']} orders, {len(initial['orders'])} exported lines, "
          f"net sales ${result['metrics']['net_sales']:,.2f}, expected card payout ${result['metrics']['expected_card_payout']:,.2f}")
    print("Fixture integrity checks passed; no model runs have been performed.")


if __name__ == "__main__":
    main()
