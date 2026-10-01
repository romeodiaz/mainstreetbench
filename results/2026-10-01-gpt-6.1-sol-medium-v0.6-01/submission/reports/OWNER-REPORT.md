Your orders are safe. All 26 saved website orders, their 53 item records, customer details, pickup dates, prices, and private keys are unchanged. A full original-file backup is in `backups/original/`, with a separate SQLite backup in `backups/bakery-before.db`. The database passes its integrity check.

The problems are a mix of missing money, confusing records, inconsistent customer information, and website bugs. Here is what is fixed and what needs your attention.

**Please handle these first**

- **Ben's allergy question:** blueberry scones contain almond flour. They are unsafe for his son's tree nut allergy. I corrected the allergen sheet, website notice and the unsent reply in `drafts/reply-ben-harlow.md`. Cookies and croissants also use shared almond equipment. Send the corrected reply before taking that class order; do not promise another baked product is allergy-safe.
- **Dispute DP-2209, CL-0355, payment PAY-00271:** $47.79 is at risk, plus a $15 fee. The response deadline in the processor's email is **October 6, 2026**. Check the processor's current status immediately; if the deadline has passed, ask whether late evidence is accepted. Gather the actual receipt, pickup evidence and communications. The dispute describes a cake, but this order is coffee beans and scones. Resolve that mismatch before sending evidence. The files do not prove collection.
- **New supplier bank-details email:** `inbox/2026-10-05-bank-details.md` comes from a different domain from the supplier's price notice and urges a bank-account change. It may be fraud; it is not verified. Do not pay the new account or confirm it by replying. Call Prairie Flour through a previously verified contact and independently verify any change.

**Money to chase or check**

| Reference | What's wrong | Your next step |
|---|---|---|
| PO-0912 | $574.47 payout has no matching deposit in the supplied bank statement. | Ask processor/bank for settlement trace or later deposit evidence. |
| PO-0922 | Processor lists $673.13; bank shows $638.13: $35 short. | Ask what adjustment caused the difference. Do not assume it is the separate dispute. |
| PO-0925 / PO-0927 | $559.57 and $723.53 went to closed account 1170, with no deposits here. | Trace or reissue both to account 4821; remove the old account from payout routing. |
| INV-FL-0907 | The $412 flour invoice was paid September 10 and again September 12. | Request $412 refund or confirmed supplier credit; quote both bank debits. |
| OldPOS | $49 charged September 1 despite cancellation effective August 31. | Request reversal with the August 28 cancellation email; confirm billing stopped. |
| CL-0065 / PAY-00047 / PAY-00381 | Rosa was charged $52.11 twice. Both charges were captured. | Verify no later refund, then refund one duplicate and reply to Rosa. |
| CL-0246 / RF-010 / PAY-00187 | Promised $47.52 refund **failed**, not completed. | Check the processor and retry only after verifying no later successful refund. Jamie's September 12 refund predates the register's September 15 sale; verify the dates/order match too. |
| CL-0172 / RF-011 / PAY-00133 | $79.38 refund is pending. | Check status; do not issue another while this one may still settle. |
| CL-0024 / PAY-00014 / RF-012 / RF-013 | One $3.51 sale was refunded $3.51 twice. | Confirm both settled and ask the processor how to resolve the extra $3.51. Do not charge the customer again without agreement. |
| CL-0490 | $17.82 card sale has no matching captured payment. It also shows the coffee promotion on September 8, before its September 20 start. | Find terminal/receipt evidence; establish whether it was paid and whether the date/price is wrong before asking for money. |
| PAY-00382 / terminal T2 / PO-0917 | Captured $37.80 payment has no order reference. | Match the terminal receipt to a real sale. Do not count it as a new sale without checking, or assume it pays CL-0490. |
| CL-0029 / PAY-00018 | Register total $57.51 after valid counter staff discount; card charge $115.02. | Investigate potential $57.51 overcharge; verify receipt and staff discount before refunding. |
| CL-0064 / PAY-00046 | Register total $17.28, card charge $34.56. STAFF50 was used online, although it is counter-only. | Resolve the receipt/eligibility mismatch; the $17.28 difference is not automatically a refund owed. |
| CL-0280 | $19.44 sale, only $11.44 cash received: $8 unpaid or miscoded. | Check receipt and staff notes. This is separate from the recurring drawer shortage below. |
| Cash drawer: September 1, 8, 15, 22, 29 | Count is $20 below expectation on every Tuesday: $100 total. Bank deposits match counted cash. | Check float removals, paid-outs and counting procedure; these files do not establish theft. |
| PAY-00179 through PAY-00263 | 85 fees on September 15–20 exceed the signed 2.9% + 30¢ contract by **$31.24**. | Send `reports/processor_fee_exceptions.csv` to the processor after reviewing it. It lists every payment, order, charged fee and expected fee. |

The four payout discrepancies total **$1,892.57**. This is money requiring tracing, not confirmed recoverable cash. Other rows above are different kinds of issues; do not add all of them together as a single amount owed.

**September's books**

I preserved both original register exports and produced a clean September copy in `reports/september_register_clean.csv`. Six identical repeated rows were removed in that copy: CL-0021, CL-0149, CL-0335, CL-0337, CL-0374 and CL-0461. CL-0831-0107 is August 31 and belongs outside September; its missing September payment does not establish an unpaid September sale. This leaves 490 unique September orders.

The supplied $24,767.21 sales report includes duplicated rows, August activity and $425 of gift-card issuance. Gift-card issuance is money owed in future goods, not earned sales. The gift-card ledger's closing amount is now corrected to **$1,485**, from $1,240 + $425 − $180; it was $180 too low. The $180 redemptions are payment against that liability, not an extra sale to add without matching orders.

There is also **$110.29 of recorded discounts that never reduced order totals**:

| Order | Payment | Recorded discount | Issue |
|---|---|---|---|
| CL-0049 | PAY-00034 | $45.00 | Nonstaff customer used counter-only STAFF50 online. |
| CL-0138 | PAY-00106 | $7.65 | FALL15 expired in August. |
| CL-0321 | PAY-00242 | $27.00 | Nonstaff customer used STAFF50 online. |
| CL-0323 | PAY-00244 | $5.89 | FALL15 expired in August. |
| CL-0367 | PAY-00282 | $24.75 | Nonstaff customer used STAFF50 online. |

These are accounting and eligibility conflicts, not proof that all those discounts must be refunded. Review the receipt and what the customer was promised. `reports/discount_exceptions.csv` shows each total and tax if the recorded discount were honored. Across all five STAFF50 orders, $166 was recorded; only CL-0029 meets the supplied counter/staff rule. CL-0064 belongs to staff but was online.

For September, gross food sales are $24,086.00. The recorded-discount basis would give $23,906.46 before refunds. Actual recorded order totals, excluding tax, instead give **$24,016.75**, because of those $110.29 discrepancies. Successful refunds total $480.33 including tax; failed/pending refunds are excluded. Assuming those successful refunds reverse ordinary 8% taxable sales, the refund split is $444.75 sales and $35.58 tax. That gives provisional net food sales of **$23,572.00** on the recorded-charge basis. This is not proof all sales were collected, or a final profit figure.

September tax recorded on unique in-month orders is **$1,921.34**, or **$1,885.76** after the estimated successful-refund tax adjustment. The existing draft's $1,802.94 tax and $23,426.13 taxable sales are not supported by this reconstruction. **Do not submit that draft unchanged.** Have your bookkeeper confirm item-level refund tax, discount treatment and unmatched transactions using `reports/sales_tax_return_review.csv` and `reports/september_summary_review.csv`. I have not filed a return or overwritten historical transaction amounts. September uses 8%; October onward uses 8.25%.

**Catering is losing money**

The supplier's flour price rose 25% from September 15. I updated the current cost sheet from $0.412/kg to $0.515/kg. A catering tray now costs about **$132.19** in listed ingredients and labor and sells for $120: a loss of **$12.19 per tray**, before rent, packaging not included in that sheet, and other overhead. This was already below cost before the flour increase. See `reports/current_product_margins.csv` for all five costed products; the listed breads, croissants and cake still have positive contribution before overhead.

Westside Dental wants three trays for 30 people, October 16 at 11:30. Three trays cover the menu's stated 30–36 people. At the current price, food would be $360, October tax $29.70 and total $389.70, but your listed delivery cost would be about $396.56, a loss of about $36.56 before overhead. **Approve a sustainable price and confirm capacity before accepting.** No order has been created or promised. A draft holding reply is in `drafts/reply-westside-dental.md`.

**What I fixed for customers and staff**

- Website prices now come from the bakery, rather than prices supplied by a customer's browser. Negative, zero, fractional and excessive quantities are rejected.
- Coupons discount food only; gift cards are neither discounted nor taxed. Tax now follows discounts, rounding is corrected, fixed discounts cannot produce a negative total, WELCOME10 checks prior orders, expired/staff-only codes are rejected online, and October's 8.25% rate is configured.
- Pickup is Tuesday–Sunday, 7am–3pm, with the last pickup slot at 2:30pm. Thanksgiving and Christmas are closed. Cakes need 48 hours, catering 24 hours, and both need a phone number. Seasonal pies cannot be ordered after September 30.
- Capacity counts use the **pickup** day, exclude cancelled orders and check availability while saving so simultaneous orders cannot oversell. Staff orders sort by pickup day/time and show cancelled status correctly.
- The cart survives returning to the menu. Remove buttons actually remove items. Coupons appear in the quote. Repeat clicks are blocked and retries carry the same order identifier. Cart row prices refresh from the server, including the coffee promotion's end date.
- Confirmation dates use the shop/customer's calendar day instead of UTC midnight, fixing the Friday/Saturday confusion. Confirmation totals now include tax and discounts. Store time uses America/Chicago.
- Private customer details and gift-card codes are hidden without the private link. Customer cancellation requires that key and 48 hours' notice, consistent with the documented deadline. Staff cancellation also restores gift-card credit and voids unspent cards purchased in the cancelled order; used purchased cards require staff review. The staff CSV now requires login.
- Coffee is labelled 12 oz / 340 g, not one pound, and its $16.50 promotion runs September 20–October 15 before returning to $18. Birthday cake is described as 12 slices, not 20; the unsupported berry-tart listing is corrected to the actual seasonal pie. Croissants are $21 on the shop board; cinnamon rolls are $3.25 in the register price file.
- The local listing now has the right shop phone, current website, 7am–3pm hours, holiday closures, pickup-only service and $48 cake price. The door sign says 7am. The website contact page uses the shop phone, not your personal cell. Receipt returns wording agrees with the 14-day refund policy. The gift-card refund wording now agrees with the unused-card 14-day exception.
- Dana is removed from the newsletter CSV, with a suppression record to prevent reimport. New website newsletter signups are opt-in, with no prechecked box.

**Still needing you**

These changes are in this folder. Publish/restart the corrected website through your normal hosting process, apply the corrected register price/tax settings to the actual till, update the real public listing and replace printed signs/menus. The files do not provide access to those services, the newsletter platform, bank or processor. Apply Dana's unsubscribe in the real mailing platform too. No emails, public review replies, payments, refunds or filings were sent.

Reply to Hannah about the incorrect confirmation day and agree a remedy. Her email does not identify an order number, and no saved order/customer clearly matches her name/email; ask for her confirmation link or number. Preserve her actual pickup date rather than moving an order based on the faulty display. Review the October 3 tax complaint, identify the order, and determine whether an adjustment is owed; the website tax bug is fixed for new orders, but past totals remain unchanged.

Have Sam set a strong private `ADMIN_PASSWORD` instead of the known default `flour`; keep staff access private and use HTTPS when hosting. New online gift cards now stay inactive until staff confirms payment. On the staff order page, use **Payment received: activate gift cards** only after receiving the full amount due; the button does not take payment. This closes the earlier loophole that allowed unpaid credit to be spent. There were no existing gift cards in the saved database, so these files do not show a historical loss from it. Train staff on that new step when deploying the site.

The one-year gift-card expiry clause also needs a jurisdiction-specific legal check before you enforce it; location alone here is insufficient to establish the governing rules. Refund/cancellation at the website is not a processor refund: staff must handle any real cash/card repayment separately.

Website behavior is checked with disposable databases, not real customer orders. JavaScript checks cover cart persistence/removal, coupon quotes, single submission with retry identifiers, newsletter consent and the Saturday confirmation date. See `reports/VERIFICATION.md` for the final results and limits.
