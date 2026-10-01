"""Store-local pickup rules."""
import datetime as dt

DAILY_LIMITS = {'CAKE48': 6, 'CATER120': 4, 'PIE32': 8}
SLOTS = [f'{hour:02d}:{minute:02d}' for hour in range(7, 15) for minute in (0, 30)]


def eligible_slots(date, lines, now):
    if date.weekday() == 0:
        return []
    lead = dt.timedelta(days=2) if any(l['sku'] in ('CAKE48', 'CATER120') for l in lines) else dt.timedelta(hours=2)
    return [s for s in SLOTS if dt.datetime.fromisoformat(f'{date.isoformat()}T{s}') >= now + lead]
