"""Black-box harness: start a submitted site and talk to it over HTTP only.

SITE_ROOT points at the site under test (a directory containing the `bakery` package).
The legacy database is always built with the original starter code, never the submission.
"""

import base64
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
STARTER = TASK / "starter"
SITE = Path(os.environ.get("SITE_ROOT", STARTER)).resolve()
NOW = "2026-10-08T09:10:00"          # Thursday
SATURDAY = "2026-10-10"
SUNDAY = "2026-10-11"
MONDAY = "2026-10-12"
TODAY = "2026-10-08"
PASSWORD = "grader-secret"
LEGACY_NOW = "2026-10-01T10:00:00"


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Site:
    def __init__(self, root: Path, db: Path, now: str = NOW):
        self.port = free_port()
        env = {**os.environ, "CORNERLOAF_NOW": now, "ADMIN_PASSWORD": PASSWORD, "PYTHONDONTWRITEBYTECODE": "1"}
        self.proc = subprocess.Popen(
            [sys.executable, "-m", "bakery.server", "--port", str(self.port), "--db", str(db)],
            cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        deadline = time.time() + 10
        while time.time() < deadline:
            if self.proc.poll() is not None:
                raise RuntimeError("Site exited on startup: " + self.proc.stderr.read().decode()[-2000:])
            try:
                socket.create_connection(("127.0.0.1", self.port), timeout=0.2).close()
                return
            except OSError:
                time.sleep(0.05)
        self.stop()
        raise RuntimeError("Site did not start within 10 seconds")

    def stop(self) -> None:
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
        self.proc.stderr.close()

    def call(self, method: str, path: str, body=None, admin: bool = False):
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", method=method,
                                         data=None if body is None else json.dumps(body).encode())
        request.add_header("Content-Type", "application/json")
        if admin:
            request.add_header("Authorization", "Basic " + base64.b64encode(f"staff:{PASSWORD}".encode()).decode())
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                raw, status = response.read(), response.status
        except urllib.error.HTTPError as error:
            raw, status = error.read(), error.code
        try:
            return status, json.loads(raw)
        except ValueError:
            return status, raw.decode("utf-8", "replace")


def order_body(items=(("BREAD9", 2),), date=SATURDAY, slot="10:00", promo=None, name="Ana Lopez") -> dict:
    body = {"customer": {"name": name, "email": "ana@example.com", "phone": "555-0100"},
            "pickup_date": date, "pickup_slot": slot, "items": [{"sku": s, "qty": q} for s, q in items]}
    if promo:
        body["promo_code"] = promo
    return body


def build_legacy_db(path: Path) -> list[dict]:
    """Create a database with the original schema and real-looking orders, using the starter code."""
    site = Site(STARTER, path, now=LEGACY_NOW)
    try:
        orders = []
        for items, date in ((("CAKE48", 3), ("BREAD9", 1)), SATURDAY), ((("CAKE48", 2),), SATURDAY), \
                           ((("COFFEE18", 1),), SUNDAY), ((("CAKE48", 4),), SATURDAY):
            body = order_body(items, date=date, name="Legacy Customer")
            del body["pickup_slot"]
            status, order = site.call("POST", "/api/orders", body)
            assert status == 201, order
            orders.append(order)
        status, cancelled = site.call("POST", f"/admin/api/orders/{orders[-1]['id']}/cancel", admin=True)
        assert status == 200
        orders[-1] = cancelled
        return orders
    finally:
        site.stop()


class SiteCase(unittest.TestCase):
    """Fresh site and database per test."""

    db_source: Path | None = None

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db = self.tmp / "bakery.db"
        if self.db_source is not None:
            shutil.copy(self.db_source, self.db)
        self.site = Site(SITE, self.db)

    def tearDown(self):
        self.site.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def restart(self):
        self.site.stop()
        self.site = Site(SITE, self.db)

    def call(self, *args, **kwargs):
        return self.site.call(*args, **kwargs)

    def place(self, *args, **kwargs):
        return self.call("POST", "/api/orders", order_body(*args, **kwargs))

    def assertMoney(self, actual, expected: str, label: str = ""):
        self.assertIsInstance(actual, (int, float), label)
        self.assertEqual(Decimal(str(actual)), Decimal(expected), label)

    def admin_orders(self, date=None) -> list:
        status, data = self.call("GET", "/admin/api/orders" + (f"?date={date}" if date else ""), admin=True)
        self.assertEqual(status, 200)
        return data["orders"]


class LegacyCase(SiteCase):
    """Fresh copy of a database created by the original site, with existing orders."""

    @classmethod
    def setUpClass(cls):
        cls.legacy_dir = Path(tempfile.mkdtemp())
        cls.db_source = cls.legacy_dir / "legacy.db"
        cls.legacy_orders = build_legacy_db(cls.db_source)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.legacy_dir, ignore_errors=True)
