#!/usr/bin/env python3
"""Build a solver workspace: the starter site, the tickets, the owner's prompt and a live database.

The workspace never contains hidden tests, the reference solution or the evaluator.

    python3 tasks/ordering-site/package.py --out /path/to/workspace
"""

import argparse
import hashlib
import json
import random
import shutil
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK / "hidden_tests"))
from sitectl import LEGACY_NOW, STARTER, Site  # noqa: E402

PROMPT = (TASK / "prompt.txt").read_text(encoding="utf-8")
FIRST_NAMES = ["Maria", "James", "Priya", "Daniel", "Aisha", "Tom", "Keiko", "Luis", "Grace", "Omar", "Hannah", "Ivy"]
LAST_NAMES = ["Lopez", "Chen", "Patel", "Okafor", "Rahman", "Walsh", "Tanaka", "Garcia", "Kim", "Haddad", "Reed"]
PICKUP_DATES = ["2026-10-02", "2026-10-03", "2026-10-04", "2026-10-09", "2026-10-10", "2026-10-11",
                "2026-10-14", "2026-10-17"]
ITEMS = ["BREAD9", "BAGUETTE5", "BAGEL225", "CROISSANT21", "CINNAMON325", "SCONE375", "COOKIE12", "PIE32",
         "CAKE48", "CATER120", "COFFEE18", "GIFT25"]


def seed_orders(site: Site, rng: random.Random, count: int = 30) -> list:
    orders = []
    for n in range(count):
        first, last = rng.choice(FIRST_NAMES), rng.choice(LAST_NAMES)
        lines = {}
        for sku in rng.sample(ITEMS, rng.randint(1, 3)):
            lines[sku] = 1 if sku in {"CAKE48", "CATER120", "PIE32"} else rng.randint(1, 4)
        body = {"customer": {"name": f"{first} {last}", "email": f"{first}.{last}{n}@example.com".lower(),
                             "phone": f"555-01{n:02d}-{rng.randint(1000, 9999)}"},
                "pickup_date": rng.choice(PICKUP_DATES), "items": [{"sku": s, "qty": q} for s, q in lines.items()]}
        if rng.random() < 0.25:
            body["promo_code"] = rng.choice(["WELCOME10", "FALL15", "FIVEOFF"])
        status, order = site.call("POST", "/api/orders", body)
        assert status == 201, order
        orders.append(order)
    for order in rng.sample(orders, 3):
        site.call("POST", f"/admin/api/orders/{order['id']}/cancel", admin=True)
    return orders


def package(out: Path, seed: int = 20261008) -> dict:
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} is not empty")
    out.mkdir(parents=True, exist_ok=True)
    shutil.copytree(STARTER, out, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.db"))
    shutil.copytree(TASK / "tickets", out / "tickets")
    (out / "data").mkdir()
    site = Site(STARTER, out / "data" / "bakery.db", now=LEGACY_NOW)
    try:
        orders = seed_orders(site, random.Random(seed))
    finally:
        site.stop()
    manifest = {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(out.rglob("*")) if p.is_file()}
    (out.parent / f"{out.name}-prompt.txt").write_text(PROMPT, encoding="utf-8")
    return {"workspace": str(out), "orders_in_live_db": len(orders), "files": manifest}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True, help="Empty folder to create the workspace in")
    parser.add_argument("--seed", type=int, default=20261008)
    args = parser.parse_args()
    result = package(args.out.resolve(), args.seed)
    print(json.dumps({k: v for k, v in result.items() if k != "files"}, indent=2))
    print(f"Prompt to send: {args.out.resolve().parent / (args.out.name + '-prompt.txt')}")
    print(f"{len(result['files'])} workspace files; record their hashes in the scorecard.")


if __name__ == "__main__":
    main()
