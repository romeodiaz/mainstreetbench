"""Run: python3 check.py [output_directory]. No external packages required."""
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

def check(root):
    for name in ('clean_orders.csv', 'customers.csv', 'cleaning_log.md', 'dashboard.html', 'check.py'):
        assert (root / name).is_file(), f'Missing {name}'
    orders = list(csv.DictReader((root / 'clean_orders.csv').open(newline='')))
    customers = list(csv.DictReader((root / 'customers.csv').open(newline='')))
    match = re.search(r'<script id="dashboard-data" type="application/json">(.*?)</script>', (root / 'dashboard.html').read_text(), re.S)
    assert match, 'Dashboard data missing'
    actual = json.loads(match[1])
    today = date(2026, 9, 30)
    cutoff = (today - timedelta(days=90)).isoformat()
    months = defaultdict(int)
    products = defaultdict(lambda: {'units': 0, 'revenue_cents': 0})
    grouped = defaultdict(list)
    ids = set()
    unconfirmed = 0
    for r in orders:
        assert r['Order ID'] not in ids, 'Duplicate order ID'
        ids.add(r['Order ID'])
        dt = date.fromisoformat(r['Order Date'])
        assert dt.isoformat() == r['Order Date'], 'Date format'
        assert re.fullmatch(r'\(\d{3}\) \d{3}-\d{4}', r['Phone']), 'Phone format'
        cents = int(Decimal(r['Total']) * 100)
        qty = int(r['Qty'])
        Decimal(r['Unit Price'])
        if dt > today:
            assert 'future_date' in r['Flags'], 'Unflagged future date'
            unconfirmed += cents
        else:
            months[dt.isoformat()[:7]] += cents
        products[r['Product']]['units'] += qty
        products[r['Product']]['revenue_cents'] += cents
        grouped[r['Customer ID']].append(r)
    computed_customers = []
    for cid, group in sorted(grouped.items()):
        dates = [r['Order Date'] for r in group if int(r['Qty']) > 0 and date.fromisoformat(r['Order Date']) <= today]
        computed_customers.append({'id': cid, 'name': group[0]['Customer Name'], 'email': group[0]['Email'], 'phone': group[0]['Phone'],
                                   'orders': sum(int(r['Qty']) > 0 for r in group),
                                   'revenue_cents': sum(int(Decimal(r['Total']) * 100) for r in group),
                                   'last_order': max(dates) if dates else '',
                                   'recency_uncertain': any(date.fromisoformat(r['Order Date']) > today for r in group)})
    exported = sorted([{'id': c['Customer ID'], 'name': c['Name'], 'email': c['Email'], 'phone': c['Phone'],
                        'orders': int(c['Number of Orders']), 'revenue_cents': int(Decimal(c['Net Revenue']) * 100),
                        'last_order': c['Last Order Date'], 'recency_uncertain': c['Recency Uncertain'] == 'yes'} for c in customers], key=lambda c: c['id'])
    assert exported == computed_customers, 'Customers CSV differs from order rollups'
    expected = {'as_of': today.isoformat(), 'cutoff': cutoff,
                'revenue_cents': sum(int(Decimal(r['Total']) * 100) for r in orders), 'transactions': len(orders),
                'sales_orders': sum(int(r['Qty']) > 0 for r in orders), 'refunds': sum(int(r['Qty']) < 0 for r in orders),
                'customer_count': len(grouped), 'unconfirmed_date_cents': unconfirmed,
                'monthly': dict(sorted(months.items())), 'products': dict(sorted(products.items())),
                'top_customers': sorted(computed_customers, key=lambda c: (-c['revenue_cents'], c['id']))[:10],
                'inactive_customers': sorted([c for c in computed_customers if c['last_order'] < cutoff and not c['recency_uncertain']], key=lambda c: (c['last_order'], c['id']))}
    for key, value in expected.items():
        assert actual.get(key) == value, f'Dashboard mismatch: {key}'
    assert sum(months.values()) + unconfirmed == expected['revenue_cents'], 'Monthly reconciliation'
    print(f"PASS: {len(orders)} transactions, {len(customers)} customers, ${expected['revenue_cents']/100:,.2f} net receipts; all dashboard aggregates and customer rollups match.")

if __name__ == '__main__':
    try:
        check(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent)
    except Exception as e:
        print(f'FAIL: {e}')
        sys.exit(1)
