"""Ticket 2: pickup slots, capacity, notice, closed days, admin order and existing orders."""

import re

from harness import MONDAY, NOW, SATURDAY, SUNDAY, TODAY, LegacyCase, SiteCase, order_body

ALL_SLOTS = [f"{h:02d}:{m:02d}" for h in range(7, 15) for m in (0, 30)]


class PickupTimes(SiteCase):
    def slots(self, date):
        status, data = self.call("GET", f"/api/slots?date={date}")
        self.assertEqual(status, 200, data)
        return data

    def test_slots_for_an_open_day(self):
        data = self.slots(SATURDAY)
        self.assertEqual((data["date"], data["open"]), (SATURDAY, True))
        self.assertEqual([s["time"] for s in data["slots"]], ALL_SLOTS)
        self.assertTrue(all(s["remaining"] == 4 and s["available"] for s in data["slots"]))

    def test_closed_monday(self):
        self.assertEqual(self.slots(MONDAY), {"date": MONDAY, "open": False, "slots": []})
        status, data = self.place(date=MONDAY, slot="10:00")
        self.assertEqual(status, 400, data)
        self.assertEqual(self.call("GET", "/api/slots?date=next-week")[0], 400)

    def test_today_respects_two_hours_notice(self):
        available = {s["time"]: s["available"] for s in self.slots(TODAY)["slots"]}
        self.assertFalse(any(available[t] for t in ALL_SLOTS if t <= "11:00"))
        self.assertTrue(all(available[t] for t in ALL_SLOTS if t >= "11:30"))
        self.assertEqual(self.place(date=TODAY, slot="11:00")[0], 400)
        self.assertEqual(self.place(date=TODAY, slot="11:30")[0], 201)

    def test_slot_is_required_and_must_be_a_real_slot(self):
        body = order_body()
        del body["pickup_slot"]
        self.assertEqual(self.call("POST", "/api/orders", body)[0], 400)
        for slot in ("07:15", "15:00", "06:30", "noon", ""):
            with self.subTest(slot=slot):
                self.assertEqual(self.place(slot=slot)[0], 400)
        self.assertEqual(self.admin_orders(), [])

    def test_slot_is_saved_on_the_order(self):
        status, order = self.place(slot="14:30")
        self.assertEqual((status, order["pickup_slot"]), (201, "14:30"))
        self.assertEqual(self.call("GET", f"/api/orders/{order['id']}")[1]["pickup_slot"], "14:30")

    def test_four_orders_per_slot_and_cancelling_frees_one(self):
        placed = [self.place(slot="09:00", name=f"Customer {n}") for n in range(4)]
        self.assertTrue(all(status == 201 for status, _ in placed))
        status, data = self.place(slot="09:00")
        self.assertEqual(status, 409, data)
        self.assertIsInstance(data.get("error"), str)
        slot = next(s for s in self.slots(SATURDAY)["slots"] if s["time"] == "09:00")
        self.assertEqual((slot["remaining"], slot["available"]), (0, False))
        self.assertEqual(self.place(slot="09:30")[0], 201)
        self.assertEqual(self.place(date=SUNDAY, slot="09:00")[0], 201)
        self.call("POST", f"/admin/api/orders/{placed[0][1]['id']}/cancel", admin=True)
        self.assertEqual(self.place(slot="09:00")[0], 201)

    def test_cakes_and_catering_need_two_days(self):
        # Now is Thursday 09:10, so 48 hours runs to Saturday 09:10.
        for sku in ("CAKE48", "CATER120"):
            with self.subTest(sku=sku):
                self.assertEqual(self.place([(sku, 1)], slot="09:00")[0], 400)
                self.assertEqual(self.place([(sku, 1), ("BREAD9", 1)], slot="08:30")[0], 400)
                self.assertEqual(self.place([(sku, 1)], slot="09:30")[0], 201)
        self.assertEqual(self.place([("PIE32", 1)], date="2026-10-09", slot="09:00")[0], 201)
        self.assertEqual(self.place([("BREAD9", 1)], slot="07:00")[0], 201)

    def test_admin_lists_orders_in_pickup_order(self):
        plan = [(SUNDAY, "08:00"), (SATURDAY, "13:00"), (SATURDAY, "07:30"), (SATURDAY, "13:00"), (SUNDAY, "07:00")]
        ids = [self.place(date=d, slot=s)[1]["id"] for d, s in plan]
        expected = [ids[2], ids[1], ids[3], ids[4], ids[0]]
        listed = self.admin_orders()
        self.assertEqual([o["id"] for o in listed], expected)
        self.assertEqual([o["pickup_slot"] for o in listed], ["07:30", "13:00", "13:00", "07:00", "08:00"])
        self.assertEqual([o["id"] for o in self.admin_orders(SATURDAY)], expected[:3])
        status, page = self.call("GET", "/admin", admin=True)
        positions = [page.index(f'data-order-id="{i}"') for i in expected]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("13:00", page)

    def test_checkout_has_pickup_time_picker(self):
        status, page = self.call("GET", "/checkout")
        self.assertEqual(status, 200)
        self.assertRegex(page, re.compile(r"<select[^>]*name=[\"']pickup_slot[\"']", re.I))


class ExistingOrdersKeepWorking(LegacyCase):
    def test_existing_orders_survive_the_upgrade(self):
        listed = {o["id"]: o for o in self.admin_orders()}
        for old in self.legacy_orders:
            with self.subTest(order=old["id"]):
                self.assertIn(old["id"], listed)
                now = listed[old["id"]]
                self.assertIsNone(now.get("pickup_slot", "missing"))
                for field in ("status", "pickup_date", "subtotal", "tax", "total"):
                    self.assertEqual(now[field], old[field], field)
                self.assertEqual([(i["sku"], i["qty"]) for i in now["items"]],
                                 [(i["sku"], i["qty"]) for i in old["items"]])
        self.assertEqual(self.call("GET", f"/api/orders/{self.legacy_orders[0]['id']}")[1]["pickup_slot"], None)

    def test_new_orders_work_alongside_existing_ones(self):
        status, order = self.place([("BREAD9", 1)], slot="07:00")
        self.assertEqual((status, order.get("pickup_slot")), (201, "07:00"), order)
        self.assertGreater(order["id"], max(o["id"] for o in self.legacy_orders))
        saturday = [o["id"] for o in self.admin_orders(SATURDAY)]
        legacy_saturday = [o["id"] for o in self.legacy_orders if o["pickup_date"] == SATURDAY]
        self.assertEqual(saturday, legacy_saturday + [order["id"]])
        self.restart()
        self.assertEqual(len(self.admin_orders()), len(self.legacy_orders) + 1)
