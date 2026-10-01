"""Ticket 7: change quantities or remove items at checkout; the order matches the edited cart."""

from harness import SiteCase


class ChangeTheCart(SiteCase):
    def items(self, attempt):
        return sorted((i["sku"], i["qty"]) for i in self.saved(attempt.order_id)["items"])

    def test_lower_a_quantity(self):
        attempt = self.placed([("BREAD9", 3), ("COOKIE12", 1)], edits=[("Sourdough Loaf", 1)])
        self.assertEqual(self.items(attempt), [("BREAD9", 1), ("COOKIE12", 1)])

    def test_raise_a_quantity(self):
        attempt = self.placed([("BREAD9", 1)], edits=[("Sourdough Loaf", 4)])
        self.assertEqual(self.items(attempt), [("BREAD9", 4)])

    def test_take_something_out(self):
        attempt = self.placed([("BREAD9", 1), ("COOKIE12", 2)], edits=[("Cookie Box", 0)])
        self.assertEqual(self.items(attempt), [("BREAD9", 1)])
        self.assertMoney(self.saved(attempt.order_id)["total"], "9.72")

    def test_emptied_cart_cannot_be_ordered(self):
        attempt = self.order([("BREAD9", 1)], edits=[("Sourdough Loaf", 0)])
        self.assertFalse(attempt.placed)
        # Only a real removal counts: the bread must have been added and then taken out.
        self.assertNotIn("could not add", attempt.reason)
        self.assertNotIn("could not change", attempt.reason)
        self.assertEqual(self.admin_orders(), [])
