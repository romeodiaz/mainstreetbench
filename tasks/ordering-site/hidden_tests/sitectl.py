"""Start and stop a site process and call its HTTP API. No browser needed (packaging uses this too)."""

import base64
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
STARTER = TASK / "starter"
SITE = Path(os.environ.get("SITE_ROOT", STARTER)).resolve()
NOW = "2026-10-08T09:10:00"          # Thursday
TODAY = "2026-10-08"
FRIDAY = "2026-10-09"
SATURDAY = "2026-10-10"
SUNDAY = "2026-10-11"
MONDAY = "2026-10-12"
PASSWORD = "grader-secret"
LEGACY_NOW = "2026-10-01T10:00:00"
WAIT_MS = 5000


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Site:
    def __init__(self, root: Path, db: Path, now: str = NOW):
        self.port = free_port()
        self.base = f"http://127.0.0.1:{self.port}"
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
        request = urllib.request.Request(self.base + path, method=method,
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


def build_legacy_db(path: Path) -> list[dict]:
    """Create a database with the original schema and existing orders, using the starter's own API."""
    site = Site(STARTER, path, now=LEGACY_NOW)
    try:
        orders = []
        for items, date in ((("CAKE48", 3), ("BREAD9", 1)), SATURDAY), ((("CAKE48", 2),), SATURDAY), \
                           ((("COFFEE18", 1),), SUNDAY), ((("CAKE48", 4),), SATURDAY):
            body = {"customer": {"name": "Legacy Customer", "email": "legacy@example.com", "phone": "555-0199"},
                    "pickup_date": date, "items": [{"sku": s, "qty": q} for s, q in items], "promo_code": "WELCOME10"}
            status, order = site.call("POST", "/api/orders", body)
            assert status == 201, order
            orders.append(order)
        status, cancelled = site.call("POST", f"/admin/api/orders/{orders[-1]['id']}/cancel", admin=True)
        assert status == 200
        orders[-1] = cancelled
        return orders
    finally:
        site.stop()
