"""Independent solvers that read only the solver-visible inputs and emit grader evidence.

`solve` follows the bookkeeper's notes and must earn a perfect score; it proves the
key is derivable from the exported files. `naive_solve` makes the shortcuts a
checklist-following solver would make; it must score clearly lower. Neither uses
the generator's internal ledger. Keep this file out of solver workspaces.
"""

import csv
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


def read(folder, name):
    with (Path(folder) / name).open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def cents(value):
    return int(Decimal(value) * 100)


def dollars(value):
    return float(Decimal(value) / 100)


def unique(rows, key):
    result = {}
    for row in rows:
        result.setdefault(row[key], row)
    return list(result.values())


def latest_lines(rows):
    latest = {}
    for row in rows:
        if row["line_id"] not in latest or int(row["record_version"]) > int(latest[row["line_id"]]["record_version"]):
            latest[row["line_id"]] = row
    return list(latest.values())


def attribute(lines, roster):
    first = lines[0]
    if first["customer_id"]:
        return first["customer_id"]
    email = first["customer_email"].strip().lower()
    phone = re.sub(r"\D", "", first["customer_phone"])
    cards = set(re.findall(r"CL-\d{4}", " ".join(line["notes"] for line in lines)))
    if not (email or phone or cards):
        return "WALK_IN"
    found = []
    if email:
        found.append({c["customer_id"] for c in roster if c["email"].lower() == email})
    if phone:
        found.append({c["customer_id"] for c in roster if re.sub(r"\D", "", c["phone"]) == phone})
    if cards:
        found.append({c["customer_id"] for c in roster if c["loyalty_reference"] in cards})
    found = [f for f in found if f]
    common = set.intersection(*found) if found else set()
    return next(iter(common)) if len(common) == 1 else "UNASSIGNED"


def solve(folder, month="2026-09", naive=False):
    roster = read(folder, "customers.csv")
    gift = {p["sku"] for p in read(folder, "products.csv") if p["category"] == "gift_card"}
    raw_orders, raw_payments, raw_refunds = (read(folder, n) for n in ("orders.csv", "payments.csv", "refunds.csv"))
    lines = raw_orders if naive else latest_lines(raw_orders)
    payments = raw_payments if naive else unique(raw_payments, "payment_id")
    refunds = raw_refunds if naive else unique(raw_refunds, "refund_id")
    by_line = {line["line_id"]: line for line in lines}
    grouped = defaultdict(list)
    for line in lines:
        grouped[line["order_id"]].append(line)
    period = {k: v for k, v in grouped.items() if naive or v[0]["ordered_at"].startswith(month)}
    owner = {k: (v[0]["customer_id"] or "WALK_IN") if naive else attribute(v, roster) for k, v in grouped.items()}
    active = [r for r in refunds if r["status"] == "succeeded" and r["completed_at"].startswith(month)]
    if naive:
        active = refunds
    accepted = [p for p in payments if (naive or p["status"] == "captured") and p["payment_at"].startswith(month)]

    orders, products, customers = {}, defaultdict(lambda: [0, 0]), defaultdict(lambda: [set(), 0])
    for order_id, order_lines in period.items():
        sales = 0
        for line in order_lines:
            if line["sku"] in gift and not naive:
                continue
            amount = int(line["quantity"]) * cents(line["unit_price"]) - cents(line["discount_amount"])
            sales += amount
            products[line["sku"]][0] += int(line["quantity"])
            products[line["sku"]][1] += amount
        customers[owner[order_id]][0].add(order_id)
        customers[owner[order_id]][1] += sales
        orders[order_id] = {"order_id": order_id,
                            "customer_id": owner[order_id] if owner[order_id].startswith("C") else "NONE",
                            "sales_before_refunds": sales,
                            "amount_due": sum(cents(line["line_total"]) for line in order_lines),
                            "captured_tenders": 0}
    for refund in active:
        source = by_line[refund["line_id"]]
        products[source["sku"]][0] -= int(refund["quantity"])
        products[source["sku"]][1] -= cents(refund["refund_sales"])
        customers[owner[source["order_id"]]][1] -= cents(refund["refund_sales"])
    unmatched = []
    for payment in payments:
        if not naive and payment["status"] != "captured":
            continue
        target = payment["order_id"]
        if not target and payment["reference"].startswith("order:") and not naive:
            target = payment["reference"][6:]
        if target in orders:
            orders[target]["captured_tenders"] += cents(payment["amount"])
        elif not target and payment in accepted:
            unmatched.append(payment)

    sales_before = sum(o["sales_before_refunds"] for o in orders.values())
    refund_sales = sum(cents(r["refund_sales"]) for r in active)
    paid_out = sum(cents(r["refund_total"]) for r in active if r["tender"] in {"card", "cash"})
    taken = sum(cents(p["amount"]) for p in accepted if p["tender"] in {"card", "cash"})
    fees = sum(cents(p["fee"]) for p in accepted)
    settled = (lambda row: row["payment_at"].startswith(month)) if naive else \
        (lambda row: row["settled_at"].startswith(month))
    payout = sum(cents(p["amount"]) - cents(p["fee"]) for p in payments
                 if p["tender"] == "card" and (naive or p["status"] == "captured") and settled(p))
    payout -= sum(cents(r["refund_total"]) - cents(r["fee_adjustment"]) for r in refunds if r["tender"] == "card"
                  and (naive or (r["status"] == "succeeded" and r["settled_at"].startswith(month))))

    exceptions = []
    if not naive:
        exceptions += [[o["order_id"]] for o in orders.values() if o["captured_tenders"] != o["amount_due"]]
        exceptions += [[p["payment_id"]] for p in unmatched if p["tender"] == "card"]
        exceptions += [[r["refund_id"]] for r in refunds if r["status"] in {"failed", "pending"}]
        exceptions += [[k] for k in period if owner[k] == "UNASSIGNED"]
    else:
        # Checklist habit: list every multi-payment order and every order without a customer ID.
        counts = defaultdict(int)
        for payment in payments:
            counts[payment["order_id"]] += 1
        exceptions += [[k] for k, n in counts.items() if k and n > 1]
        exceptions += [[k] for k, v in period.items() if not v[0]["customer_id"]]

    ranked = sorted(((cid, v) for cid, v in customers.items() if cid.startswith("C")), key=lambda kv: -kv[1][1])
    return {
        "metrics": {
            "merchandise_sales_before_refunds": dollars(sales_before),
            "successful_refund_sales": dollars(refund_sales), "net_sales": dollars(sales_before - refund_sales),
            "total_successful_refunds": dollars(paid_out), "card_processing_fees": dollars(fees),
            "expected_card_payout": dollars(payout), "net_external_receipts": dollars(taken - paid_out),
        },
        "products": [{"sku": sku, "net_units": u, "net_sales": dollars(s)} for sku, (u, s) in products.items()
                     if sku not in gift],
        "top_customers": [{"customer_id": cid, "net_sales": dollars(v[1])} for cid, v in ranked[:10]],
        "orders": [{**o, **{k: dollars(o[k]) for k in ("sales_before_refunds", "amount_due", "captured_tenders")}}
                   for o in orders.values()],
        "refunds": [{"refund_id": r["refund_id"],
                     "deducted_sales": dollars(cents(r["refund_sales"]) if r in active else 0)}
                    for r in refunds] if not naive else
                   [{"refund_id": r["refund_id"], "deducted_sales": float(r["refund_sales"])}
                    for r in unique(refunds, "refund_id")],
        "exceptions": [{"record_ids": ids, "summary": "solver flag"} for ids in exceptions],
    }


def naive_solve(folder, month="2026-09"):
    return solve(folder, month, naive=True)
