"""Customer allergy information from the kitchen-reviewed sheet in this folder."""
import csv
from pathlib import Path

SHEET = Path(__file__).resolve().parents[2] / 'menu' / 'allergens.csv'


def allergy_info(name):
    with SHEET.open(newline='', encoding='utf-8') as source:
        for row in csv.DictReader(source):
            if row['item'] == name:
                return {key: row[key] for key in ('contains', 'may_contain', 'gluten_free', 'vegan', 'notes')}
    return {'contains': 'unverified — ask the bakery', 'may_contain': 'unverified',
            'gluten_free': 'unverified', 'vegan': 'unverified', 'notes': ''}


def allergy_text(info):
    parts = []
    if info['contains']:
        parts.append('Contains: ' + info['contains'])
    if info['may_contain']:
        parts.append('May contain: ' + info['may_contain'])
    if info['notes']:
        parts.append(info['notes'])
    return '. '.join(parts)
