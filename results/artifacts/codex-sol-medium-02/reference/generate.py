"""Main Street Bench v0.1, Task 1: The Messy Spreadsheet.

Generate a deliberately messy small-business orders CSV plus an answer key.

Business: Corner Loaf Bakery (fictional, US). Data covers Oct 1 2025 - Sep 30 2026.
As-of date for "lapsed customer" questions: 2026-09-30.
"""
import csv, random, datetime as dt, os

HERE = os.path.dirname(os.path.abspath(__file__))
KEY = os.path.join(HERE, "..", "..", "answer-keys", "01-messy-spreadsheet.md")
from collections import defaultdict

random.seed(20260930)
ASOF = dt.date(2026, 9, 30)
START = dt.date(2025, 10, 1)

FIRST = ["Maria","James","Priya","Daniel","Aisha","Tom","Keiko","Luis","Grace","Omar",
         "Hannah","Victor","Nina","Samuel","Chloe","Ravi","Elena","Marcus","Sofia","Ben",
         "Fatima","Leo","Ivy","Carlos","Megan","Theo","Zara","Noah","Lily","Jonah",
         "Rosa","Kwame","Tessa","Ahmed","Julia","Owen","Mei","Diego","Clara","Isaac",
         "Amara","Felix","Ruth","Hugo","Nadia","Caleb","Jade","Emil","Lena","Paul",
         "Yara","Simon","Alice","Tariq","Maya","Arjun","Bella","Gideon","Iris","Marco"]
LAST = ["Lopez","Chen","Patel","Okafor","Rahman","Walsh","Tanaka","Garcia","Kim","Haddad",
        "Brooks","Nguyen","Petrov","Adeyemi","Martin","Iyer","Rossi","Bell","Costa","Fischer",
        "Ali","Moreau","Reed","Silva","Hughes","Park","Khan","Evans","Dubois","Grant",
        "Vega","Mensah","Lang","Farouk","Weber","Doyle","Zhang","Ortiz","Novak","Stein",
        "Obi","Klein","Shaw","Laurent","Aziz","Ward","Fox","Berg","Holm","Young",
        "Saleh","Price","Morgan","Qureshi","Cruz","Rao","Hart","Levi","Stone","Russo"]

PRODUCTS = {  # name: unit price
    "Sourdough Loaf": 9.00,
    "Croissant Box (6)": 21.00,
    "Birthday Cake": 48.00,
    "Coffee Beans 1lb": 18.00,
    "Catering Tray": 120.00,
    "Gift Card": 25.00,
}
WEIGHTS = [30, 25, 8, 20, 5, 12]
PAYMENTS = ["Card", "Card", "Card", "Cash", "Online"]

# ---- customers -------------------------------------------------------------
customers = []
used = set()
while len(customers) < 70:
    f, l = random.choice(FIRST), random.choice(LAST)
    if (f, l) in used:
        continue
    used.add((f, l))
    n = len(customers)
    customers.append({
        "first": f, "last": l, "name": f"{f} {l}",
        "email": f"{f.lower()}.{l.lower()}@example.com",
        "phone": f"555{random.randint(100,999)}01{n:02d}"[:10],
        "weight": random.choice([1, 1, 1, 2, 3, 6]),   # a few regulars
        # some customers stop ordering mid-year -> lapsed list
        "active_until": ASOF if random.random() > 0.3 else START + dt.timedelta(days=random.randint(60, 250)),
    })
# guarantee fixed "problem" customers
customers[0].update(first="Maria", last="Lopez", name="Maria Lopez",
                    email="maria.lopez@example.com", weight=6, active_until=ASOF)
customers[1].update(first="James", last="Chen", name="James Chen",
                    email="james.chen@example.com", weight=5, active_until=ASOF)
customers[2].update(first="Priya", last="Patel", name="Priya Patel",
                    email="priya.patel@example.com", weight=4, active_until=ASOF)
NO_EMAIL = {customers[10]["name"], customers[11]["name"]}  # never gave an email

# ---- clean ground-truth orders ---------------------------------------------
orders = []
oid = 10001
while len(orders) < 290:
    c = random.choices(customers, weights=[x["weight"] for x in customers])[0]
    span = (min(c["active_until"], ASOF) - START).days
    d = START + dt.timedelta(days=random.randint(0, max(span, 1)))
    prod = random.choices(list(PRODUCTS), weights=WEIGHTS)[0]
    qty = 1 if prod in ("Birthday Cake", "Catering Tray") else random.randint(1, 4)
    orders.append({"order_id": oid, "date": d, "cust": c, "product": prod, "qty": qty,
                   "price": PRODUCTS[prod], "payment": random.choice(PAYMENTS), "notes": ""})
    oid += 1
orders.sort(key=lambda o: o["date"])
for i, o in enumerate(orders):           # renumber in date order
    o["order_id"] = 10001 + i

# refunds (true data): negative rows referencing an earlier order
refunds = []
for src in random.sample(orders[20:250], 3):
    refunds.append({"order_id": None, "date": src["date"] + dt.timedelta(days=2), "cust": src["cust"],
                    "product": src["product"], "qty": -src["qty"], "price": src["price"],
                    "payment": src["payment"], "notes": f"refund for #{src['order_id']}"})
truth = orders + refunds
truth.sort(key=lambda o: o["date"])
nxt = 10001
for o in truth:
    o["order_id"] = nxt; nxt += 1
for o in truth:
    if o["notes"].startswith("refund"):
        pass
# fix refund notes to point at renumbered ids
by_obj = {id(o): o for o in truth}
for r in refunds:
    src_date = r["date"] - dt.timedelta(days=2)
    cands = [o for o in truth if o["qty"] > 0 and o["cust"] is r["cust"] and o["product"] == r["product"]
             and o["date"] == src_date and o["qty"] == -r["qty"]]
    r["notes"] = f"refund for #{cands[0]['order_id']}"

# ---- build messy rows ------------------------------------------------------
issues = defaultdict(list)   # issue key -> list of order ids / notes

def fmt_date(d, style):
    return {"iso": d.isoformat(), "us": f"{d.month}/{d.day}/{d.strftime('%y')}",
            "long": f"{d.strftime('%B')} {d.day}, {d.year}",
            "dmy": f"{d.day}-{d.strftime('%b')}-{d.year}"}[style]

def fmt_phone(p, style):
    a, b, c = p[:3], p[3:6], p[6:]
    return {"paren": f"({a}) {b}-{c}", "dots": f"{a}.{b}.{c}", "raw": p,
            "intl": f"+1 {a} {b} {c}", "dash": f"{a}-{b}-{c}"}[style]

rows = []
for o in truth:
    c = o["cust"]
    rows.append({
        "Order ID": str(o["order_id"]),
        "Order Date": o["date"].isoformat(),
        "Customer Name": c["name"],
        "Email": "" if c["name"] in NO_EMAIL else c["email"],
        "Phone": fmt_phone(c["phone"], "dash"),
        "Product": o["product"],
        "Qty": str(o["qty"]),
        "Unit Price": f"{o['price']:.2f}",
        "Total": f"{o['qty'] * o['price']:.2f}",
        "Payment": o["payment"],
        "Notes": o["notes"],
        "_truth": o,
    })
for r in rows:
    if r["_truth"]["notes"].startswith("refund"):
        issues["09 Refund rows (negative qty)"].append(r["Order ID"])
for r in rows:
    if r["Email"] == "" and r["Customer Name"] in NO_EMAIL:
        issues["05b Customers with no email anywhere (flag only)"].append(r["Order ID"])

idx = list(range(len(rows)))
pick = lambda k, pool=None: random.sample(pool if pool is not None else idx, k)

# 1. name variants for the same person (Maria Lopez, James Chen, Priya Patel)
variants = {"Maria Lopez": ["maria lopez", "M. Lopez", "Lopez, Maria", "MARIA LOPEZ"],
            "James Chen": ["james chen", "J. Chen", "Chen, James"],
            "Priya Patel": ["priya patel", "P. Patel"]}
for name, vs in variants.items():
    mine = [i for i in idx if rows[i]["Customer Name"] == name]
    for i, v in zip(random.sample(mine, len(vs)), vs):
        rows[i]["Customer Name"] = v
        issues["01 Same customer, different name spellings"].append(f"{rows[i]['Order ID']} ({v} = {name})")
    # one variant row where email is blank: must match on phone
    j = random.choice([i for i in mine if rows[i]["Customer Name"] != name])
    rows[j]["Email"] = ""
    issues["01 Same customer, different name spellings"].append(f"{rows[j]['Order ID']} (email blank - match {name} by phone)")

taken = set(i for i in idx if rows[i]["Customer Name"] != rows[i]["_truth"]["cust"]["name"])
free = lambda: [i for i in idx if i not in taken and not rows[i]["_truth"]["notes"]]

# 2. stray whitespace in names
for i in pick(8, free()):
    nm = rows[i]["Customer Name"]
    rows[i]["Customer Name"] = random.choice(["  " + nm, nm + "  ", nm.replace(" ", "  ", 1)])
    taken.add(i); issues["02 Extra spaces in customer names"].append(rows[i]["Order ID"])

# 3. mixed date formats (applies to ~60% of rows)
for i in idx:
    style = random.choices(["iso", "us", "long", "dmy"], weights=[40, 35, 15, 10])[0]
    rows[i]["Order Date"] = fmt_date(rows[i]["_truth"]["date"], style)
issues["03 Mixed date formats (ISO, M/D/YY, 'March 4, 2026', 4-Mar-2026)"].append("throughout the file")

# 4. prices stored as text with symbols
for i in pick(25):
    rows[i]["Unit Price"] = random.choice(["${}", "{} USD", "$ {}"]).format(rows[i]["Unit Price"])
    issues["04 Prices stored as text ($, USD)"].append(rows[i]["Order ID"])
for i in pick(10):
    t = float(rows[i]["_truth"]["qty"] * rows[i]["_truth"]["price"])
    if abs(t) >= 100:
        rows[i]["Total"] = f"${t:,.2f}"
        issues["04 Prices stored as text ($, USD)"].append(rows[i]["Order ID"] + " (total)")

# 5. missing emails that ARE known from other rows
for i in pick(10, [i for i in free() if rows[i]["Customer Name"] not in NO_EMAIL]):
    rows[i]["Email"] = ""
    taken.add(i); issues["05a Missing emails recoverable from other rows"].append(rows[i]["Order ID"])

# 6. product name typos / variants
typos = {"Sourdough Loaf": ["Sourdogh Loaf", "sourdough loaf"],
         "Croissant Box (6)": ["Croissant Box 6", "croissant box (6)"],
         "Coffee Beans 1lb": ["Coffee Beans 1 lb", "Cofee Beans 1lb"]}
for prod, vs in typos.items():
    mine = [i for i in free() if rows[i]["Product"] == prod]
    for i, v in zip(random.sample(mine, 3), vs + vs[:1]):
        rows[i]["Product"] = v
        issues["06 Product name typos / variants"].append(f"{rows[i]['Order ID']} ({v} = {prod})")

# 7. math errors: Total != Qty x Unit Price
for i in pick(4, free()):
    t = rows[i]["_truth"]["qty"] * rows[i]["_truth"]["price"]
    rows[i]["Total"] = f"{t + random.choice([-10, 9, 27, -4.5]):.2f}"
    taken.add(i); issues["07 Total does not equal Qty x Unit Price"].append(rows[i]["Order ID"] + f" (correct total {t:.2f})")

# 8. phone number formats
for i in idx:
    rows[i]["Phone"] = fmt_phone(rows[i]["_truth"]["cust"]["phone"],
                                 random.choice(["paren", "dots", "raw", "intl", "dash"]))
issues["08 Inconsistent phone formats"].append("throughout the file")

# 10. year typo: 2062 instead of 2026
for i in pick(2, [i for i in free() if rows[i]["_truth"]["date"].year == 2026]):
    d = rows[i]["_truth"]["date"]
    rows[i]["Order Date"] = fmt_date(d.replace(year=2062), "us" if random.random() < .5 else "iso")
    taken.add(i); issues["10 Impossible future date (2062 typo for 2026)"].append(rows[i]["Order ID"] + f" (true date {d})")

# ---- test orders and exact duplicates (added rows, not in truth) ----------
tests = []
for k in range(3):
    d = START + dt.timedelta(days=random.randint(10, 360))
    tests.append({"Order ID": str(90001 + k), "Order Date": fmt_date(d, "iso"),
                  "Customer Name": ["Test Customer", "TEST", "asdf"][k],
                  "Email": ["test@example.com", "test@test.com", ""][k], "Phone": "555-000-0000",
                  "Product": random.choice(list(PRODUCTS)), "Qty": "1", "Unit Price": "0.00" if k == 2 else "9.00",
                  "Total": "0.00" if k == 2 else "9.00", "Payment": "Card",
                  "Notes": ["test - ignore", "testing checkout", ""][k], "_truth": None})
    issues["11 Test orders that are not real sales"].append(str(90001 + k))
dups = []
for i in random.sample([i for i in idx if not rows[i]["_truth"]["notes"]], 4):
    dup = dict(rows[i]); dup["_dup"] = True
    dups.append(dup)
    issues["12 Exact duplicate rows (same Order ID twice)"].append(rows[i]["Order ID"])

allrows = rows + tests + dups
random.shuffle(allrows)   # messy files are rarely sorted

cols = ["Order ID","Order Date","Customer Name","Email","Phone","Product","Qty","Unit Price","Total","Payment","Notes"]
with open(os.path.join(HERE, "customer_orders.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader(); w.writerows(allrows)

# ---- answer key from ground truth -----------------------------------------
rev = lambda o: o["qty"] * o["price"]
monthly = defaultdict(float)
by_cust = defaultdict(float)
last = {}
prod_units = defaultdict(int); prod_rev = defaultdict(float)
for o in truth:
    monthly[o["date"].strftime("%Y-%m")] += rev(o)
    by_cust[o["cust"]["name"]] += rev(o)
    prod_units[o["product"]] += o["qty"]; prod_rev[o["product"]] += rev(o)
    if o["qty"] > 0:
        last[o["cust"]["name"]] = max(last.get(o["cust"]["name"], START), o["date"])
cutoff = ASOF - dt.timedelta(days=90)
lapsed = sorted([(n, d) for n, d in last.items() if d < cutoff], key=lambda x: x[1])

# 2062 alternative: if excluded instead of corrected
excluded_2062 = sum(rev(r["_truth"]) for r in rows if "2062" in r["Order Date"])

total = sum(rev(o) for o in truth)
with open(KEY, "w", encoding="utf-8") as fh:
    fh.write("# Main Street Bench v0.1: answer key (Corner Loaf Bakery orders)\n\n")
    fh.write("KEEP THIS OFF SCREEN until the results segment. Never give it to any agent.\n\n")
    fh.write(f"File: customer_orders.csv - {len(allrows)} rows ({len(truth)} real orders incl. {len(refunds)} refunds, "
             f"{len(tests)} test rows, {len(dups)} duplicate rows). As-of date: {ASOF}.\n\n")
    fh.write("## Planted problems (score 1 point each, 12 total)\n\n")
    fh.write("Issues 05a and 05b count as one point together (emails). Everything else is one point each.\n\n")
    labels = sorted(issues)
    for k in labels:
        fh.write(f"### {k}\n\n")
        for v in issues[k]:
            fh.write(f"- {v}\n")
        fh.write("\n")
    fh.write("## Expected handling\n\n")
    fh.write("- Refunds count as negative revenue (keep them, don't delete them).\n")
    fh.write("- Test orders and duplicate rows are removed.\n")
    fh.write("- Math errors: recompute Total = Qty x Unit Price and flag the row.\n")
    fh.write("- 2062 dates: correcting to 2026 with a flag, or excluding with a flag, both pass. Silently keeping 2062 fails.\n")
    fh.write("- Customers with no email anywhere: flag them; don't invent an address.\n\n")
    fh.write("## Correct results\n\n")
    fh.write(f"- Unique real customers: {len(set(o['cust']['name'] for o in truth))}\n")
    fh.write(f"- Total net revenue: ${total:,.2f} (if the two 2062 rows are excluded instead: ${total - excluded_2062:,.2f})\n\n")
    fh.write("### Revenue by month\n\n| Month | Net revenue |\n| --- | --- |\n")
    for m in sorted(monthly):
        fh.write(f"| {m} | ${monthly[m]:,.2f} |\n")
    fh.write("\n### Top 10 customers by net revenue\n\n| Rank | Customer | Net revenue |\n| --- | --- | --- |\n")
    for r, (n, v) in enumerate(sorted(by_cust.items(), key=lambda x: -x[1])[:10], 1):
        fh.write(f"| {r} | {n} | ${v:,.2f} |\n")
    fh.write("\n### Products\n\n| Product | Units (net) | Net revenue |\n| --- | --- | --- |\n")
    for p in sorted(prod_rev, key=lambda p: -prod_rev[p]):
        fh.write(f"| {p} | {prod_units[p]} | ${prod_rev[p]:,.2f} |\n")
    fh.write(f"\n### Lapsed customers (no order since {cutoff}): {len(lapsed)}\n\n| Customer | Last order |\n| --- | --- |\n")
    for n, d in lapsed:
        fh.write(f"| {n} | {d} |\n")

print(len(allrows), "rows;", len(truth), "truth;", "revenue", round(total, 2), "lapsed", len(lapsed))
for k in sorted(issues):
    print(k, len(issues[k]))
