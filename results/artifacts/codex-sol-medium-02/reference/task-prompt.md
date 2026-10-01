Corner Loaf Bakery is a small US bakery. Their order history for October 2025 through September 2026 is in `customer_orders.csv`, exported from their register and a spreadsheet they have kept by hand. The owner wants to understand their customers and sales. Treat 2026-09-30 as today.

Plan the work first, then build it.

Deliverables, all in an `output/` folder:

1. `clean_orders.csv`: one row per real order, with consistent dates (YYYY-MM-DD), numbers stored as numbers, standardized product names, and a stable customer ID.
2. `customers.csv`: one row per real customer, with name, email, phone in the format (555) 123-4567, number of orders, net revenue, and last order date.
3. `cleaning_log.md`: every change you made and every problem you flagged, grouped by type, with the order IDs affected.
4. `dashboard.html`: a single file that opens in a browser with no internet connection or accounts. It shows revenue by month, the top 10 customers, best-selling products, and customers who haven't ordered in the last 90 days. It must be readable on a phone screen.
5. A check script that confirms the dashboard's numbers match `clean_orders.csv`, and reports pass or fail.

Rules:

- Don't invent data. If you can't fix something with confidence, flag it in the log instead.
- Revenue should reflect what the bakery actually earned.
- Don't modify the original CSV.

You're done when the check script passes and all five deliverables exist.
