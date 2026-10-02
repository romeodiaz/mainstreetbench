"""Store-local time (America/Chicago). Tests pin it with CORNERLOAF_NOW=YYYY-MM-DDTHH:MM:SS."""

from __future__ import annotations

import datetime as dt
import os

try:
    from zoneinfo import ZoneInfo
    STORE_ZONE = ZoneInfo("America/Chicago")
except Exception:                                # no time zone data on this machine: use its own clock
    STORE_ZONE = None


def now() -> dt.datetime:
    pinned = os.environ.get("CORNERLOAF_NOW")
    if pinned:
        return dt.datetime.fromisoformat(pinned)
    if STORE_ZONE is not None:
        return dt.datetime.now(STORE_ZONE).replace(tzinfo=None, microsecond=0)
    return dt.datetime.now().replace(microsecond=0)


def today() -> dt.date:
    return now().date()
