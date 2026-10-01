"""Opening hours, pickup slots and notice rules."""

import datetime as dt

OPEN_WEEKDAYS = {1, 2, 3, 4, 5, 6}          # Tuesday–Sunday; Monday (0) closed
FIRST_SLOT = dt.time(7, 0)
LAST_SLOT = dt.time(14, 30)
SLOT_MINUTES = 30
SLOT_CAPACITY = 4
NOTICE = dt.timedelta(hours=2)
LONG_NOTICE = dt.timedelta(hours=48)
LONG_NOTICE_SKUS = {"CAKE48", "CATER120"}


def slot_times() -> list[str]:
    times, current = [], dt.datetime.combine(dt.date.min, FIRST_SLOT)
    while current.time() <= LAST_SLOT:
        times.append(current.strftime("%H:%M"))
        current += dt.timedelta(minutes=SLOT_MINUTES)
    return times


SLOTS = slot_times()


def is_open(day: dt.date) -> bool:
    return day.weekday() in OPEN_WEEKDAYS


def slot_start(day: dt.date, slot: str) -> dt.datetime:
    return dt.datetime.combine(day, dt.time.fromisoformat(slot))


def required_notice(skus) -> dt.timedelta:
    return LONG_NOTICE if LONG_NOTICE_SKUS & set(skus) else NOTICE
