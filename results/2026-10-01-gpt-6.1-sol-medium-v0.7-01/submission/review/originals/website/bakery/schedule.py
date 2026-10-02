"""Opening hours, pickup slots and notice rules."""

import datetime as dt

from . import settings


def slot_times() -> list[str]:
    times, current = [], dt.datetime.combine(dt.date.min, settings.FIRST_SLOT)
    while current.time() <= settings.LAST_SLOT:
        times.append(current.strftime("%H:%M"))
        current += dt.timedelta(minutes=settings.SLOT_MINUTES)
    return times


SLOTS = slot_times()


def is_open(day: dt.date) -> bool:
    return day.weekday() in settings.OPEN_WEEKDAYS


def slot_start(day: dt.date, slot: str) -> dt.datetime:
    return dt.datetime.combine(day, dt.time.fromisoformat(slot))


def required_notice(skus) -> dt.timedelta:
    return settings.LONG_NOTICE if settings.LONG_NOTICE_SKUS & set(skus) else settings.NOTICE


def in_season(sku: str, day: dt.date) -> bool:
    end = settings.SEASON_ENDS.get(sku)
    return end is None or day <= end
