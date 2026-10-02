I found several separate problems that together can make the bakery feel unsettled: money arriving in the wrong account, customer refunds that were not completed, misleading allergy information, and ordering errors. The repairs in this folder are complete. Publishing the updated website/listing, replacing printed materials, sending replies and moving money still need you or your service providers.

**Please handle these first.**

1. Contact Ben Harlow and Maria Santos before supplying food for their children. Scones contain almond flour. Cookies contain soy and share almond equipment; they cannot be promised safe for tree nut allergies. Maria's order is **#27, October 10 at 08:30, two cookie boxes**. Jordan Reyes also needs to know that cinnamon rolls contain milk and butter. Correct replies are in `drafts/customer-followups.md` and `drafts/reply-ben-harlow.md`; none have been sent. Replace the old allergen sheet and recall/check the 200 printed menu cards with QuickPrint before using them.
2. Ask the processor to trace **PO-0927 ($2,006.23)** and **PO-0929 ($2,355.32)**. Both went to closed account **1170** and neither appears in the supplied current-account statement. Together they total **$4,361.55**. Confirm returned funds and reissue to **4821**, and correct the processor's bank destination.
3. Check dispute **DP-2209 / CL-0203 / PAY-00157** immediately. It concerns **$68.04**, with a possible **$15 fee**. The response deadline is **October 6**; if that has passed, ask the processor about its present status and late evidence options. Collect proof of pickup if it exists. September's records do not prove the debit or the outcome.
4. Verify the suspicious flour-supplier bank-change email using Prairie Flour's existing trusted contact details, not by replying or using details in that email. Its sender domain differs from the earlier supplier email. No bank details were changed and no payment was made.

**Money that needs follow-up.** These are different kinds of issues; do not add every amount together as a single loss.

| Look up | What is wrong | Next step |
|---|---|---|
| CL-0045; PAY-00031 and PAY-00944 | Two captured charges of $25.92 for Rosa's one order | Verify current processor history and refund one extra charge; no such refund is in this folder |
| CL-0228; RF-010; PAY-00176 | The $89.64 refund failed, despite Jamie's “done” email | Retry and confirm success with customer |
| CL-0261; RF-013; PAY-00198 | Marcus was promised $96.12, but received $69.12 | Refund remaining $27.00 after checking for later activity |
| CL-0792 and CL-0794 | Coffee promotion missed; each customer overpaid $1.62 including tax | Check payment history and refund each excess |
| PAY-00315; CL-0405; PO-0910 | Fee was $3.42 instead of contractual $0.42 | Ask processor to correct the $3.00 excess |
| PO-0910 | The bank export repeats the $1,960.84 credit twice | Check the actual bank statement; count once if it is an export duplicate. An extra actual credit is not sales income |
| INV-DY-0917 | $301.15 paid September 19 and $318.60 paid September 30 under the same invoice number | Ask Valley Dairy whether these are different deliveries with a reused number, or whether a credit is due. The second payment is not proven to be a duplicate bill |
| CL-0372, CL-0651, CL-1150, CL-1184 | $134.88 total staff discounts given to three nonstaff emails and to Sam after his last day | Review overrides and restrict register access. Do not charge customers again without review |
| Cash drawers September 1, 8, 15, 22, 29 | $20 short on each date, all closed by Lee: $100 total shortages | Review receipts, float and change procedures with Lee; records do not establish theft |
| Cash drawer September 19 | $50 over, closed by Priya | Review counting and change; combined monthly variance is $50 short |

Every reference is also in `review/money-actions.csv`. Card charges, fees and completed refunds reconcile to each listed processor payout. The remaining payout problems are the bank destination and repeated bank entry. September card sales all have captured payments. The BoxRight invoice is paid; the dairy invoice INV-DY-0924 adds correctly to $284.90. No September OldPOS charge appears in the supplied bank records; keep its cancellation confirmation.

**September's books are corrected, with the original evidence retained.**

The register exports contain six repeated orders: **CL-0316, CL-0534, CL-0742, CL-0845, CL-1016 and CL-1177**. They also contain August sale **CL-0831-0107**. I excluded these from a clean September copy, leaving **1,216 unique September sales**. The raw register, bank, payment, refund and supplier exports remain intact.

Food sales after discounts and before returns are **$61,217.68**. Completed refunds total **$871.57**, including an allocated **$64.56 tax**. Food sales after those refunds are **$60,410.67**, and tax collected after them is **$4,833.15**. I corrected the September report and draft return. The earlier draft's tax figure was **$53.84 lower**. A bookkeeper should confirm the allocation and treatment of refunds before filing; pending refunds, disputes and possible future recoveries have not been booked as completed transactions. Per-refund rounding is used, so the tax total need not exactly equal 8% of the final combined sales figure.

The **$425 gift cards sold** belong in the amount the bakery owes cardholders, rather than food sales. The ledger's closing balance is now **$1,485**, calculated as $1,240 + $425 − $180; it was $180 too low. Corrected review figures and calculations are in `review/september-summary-corrected.csv`, `review/september-register-clean.csv` and `review/reconcile.py`. Originals of changed accounting documents are in `backups/`.

Flour now costs **$0.515/kg**, up from $0.412/kg (a 25% increase), and the cost sheet is updated. The $120 catering tray costs about **$132.19 in listed ingredients and labor alone**, a loss of **$12.19 before packaging, overhead and card fees**. Choose a viable catering price or recipe/staffing change before accepting more trays. I did not invent a new selling price.

**The ordering website is repaired and orders are preserved.**

All **43 original order numbers** remain. I backed up the database before changing it and checked its integrity. Other than the following clear customer requests, original orders, pickup times, private links, totals and existing payment records are retained:

| Order | Change made |
|---|---|
| #28, Gloria | October 10 at 12:30 now has 3 sourdough loaves and a croissant box. Total $51.96 using the current tax rate |
| #36, Diego | Added one baguette; October 11 at 12:30. Total $15.16 using the current tax rate |
| #39, Victor | Cancelled October 17 cake and restored $25 to his gift card, leaving $25 available |
| #41, Laura | Cancelled the exact duplicate; #40 remains for October 9 at 11:00 |

Gloria's weekly request is recorded in `admin/standing_orders.csv`. The website has no recurring-order scheduler: staff must enter later Saturdays, checking capacity each time. Nothing was cancelled for Maria without her agreement.

The website now calculates tax after coupons, uses **8.25% from October 1**, takes prices from the bakery rather than trusting customer-supplied prices, updates coffee back to $18 after October 15, respects holiday closures and 48-hour cake/catering notice, and counts daily limits by pickup date. The ended seasonal pie is hidden from the live menu; its product and any historical items are retained.

I fixed cart removal, duplicate submission/retry handling, gift-card cancellation and the pickup-day display that could show the preceding day. The clock uses Chicago time. Confirmation pages show gift-card credit and the amount to bring. New gift cards cannot be spent until staff record payment. Cancellation does not itself send a refund to a bank card.

Customer details and gift-card codes no longer appear on public order pages. Cancellation requires the private link; new links use random keys. Staff CSV exports require staff login and protect spreadsheet cells from customer-entered formulas. The site also blocks cross-site cancellation submissions. Existing private links were preserved. Anyone who may already have seen exposed information cannot be made to forget it; review access logs if available, especially for gift-card misuse.

If a custom staff password is already configured it stays in use. Otherwise, the old weak default password “flour” is replaced on restart by a generated private password in `website/data/.admin-password`. Give it only to current staff. Staff should record payment for new purchased gift cards using the existing payment-received action described in `website/README.md`.

The saved totals on older orders used the old tax rate. I did not silently change what customers were promised. `review/existing-order-tax-review.csv` lists each affected order and the tax difference for you and your bookkeeper. Some existing cinnamon-roll orders, including **#37 (six rolls)**, also retain the original $3.25 price despite the October 1 price-change instruction; see `review/existing-order-price-review.csv`. Decide how to honor quoted totals and account for the differences before changing them or giving new quotes. **Nina #30 currently owes $26.84 after her $25 gift card; Tessa #34 currently owes $22.68** under the saved totals.

Hannah's pickup complaint is consistent with the date-display bug, but her email cannot be matched to an order in this database. Ask for her order number and investigate fulfillment separately; fixing the display does not resolve her missed pickup.

**Menus, policies, marketing and staff documents are corrected.**

Cinnamon rolls are $3.50 across the current price sheets, board, menu and website. Coffee stays $16.50 through October 15, and its supplier-confirmed bag size is 12 oz. Croissants on the board are $21, matching the price sheets. The board's $21.60 two-box offer saves **10%, not 15%**; ensure staff honor that counter offer, which is not an automatic website discount. Prices are before tax. Catering notice is 48 hours.

The allergen sheet no longer says baguettes are gluten-free or scones are nut-free. It now identifies almonds, soy, sesame and the shared almond equipment. Catering filling allergens still require supplier-label checks. No gluten-free safety claim is made. The website also shows allergy information.

The cancellation policy now matches the repaired online process, including earlier notice for custom orders. Gift-card terms no longer claim short expiry or monthly fees; the cards have no expiry or inactivity fees, and unused paid cards are refundable within 14 days to match the existing refund policy. Receipt wording includes the custom cake/catering exception. These favorable terms are written in the files; make sure staff and printed materials use them.

Thanksgiving and Christmas closures are in the local listing, sign and menu. The Thanksgiving pickup promotion is on hold until you choose an open pickup date. The correct current domain and shop number remain intact; no personal phone number was published.

Sam is removed from the current staff-discount list. Remove any remaining register or service account access separately. The job advertisement no longer restricts applicants to under 30 and allows reasonable accommodation for flour handling.

The unsent newsletter has a clear subject, current prices, bakery address and an unsubscribe instruction. The checkout newsletter box is now unchecked by default. No customer was added or removed from the subscriber list based on guesswork. The sign-up notification lacks an identity; obtain the actual sign-up record first.

Tom's draft public review reply no longer exposes order, payment or health details or claims a gluten-safe loaf. Ben's dangerous draft reply is corrected. Other replies and a catering quote are in `drafts/customer-followups.md`. Westside Dental's three trays would serve about 30–36 and total $389.70 at the current menu price and tax, but this is **not a booked order**; resolve the loss-making price, get a phone number and allergen details, and recheck capacity before confirming.

**What remains outside this folder.**

Publish/restart the updated website using its existing database and a fresh backup; do not replace a database that has received newer orders with this folder's older snapshot. Publish the corrected listing, replace physical signs/menus and review QuickPrint's cards. Send the prepared replies and handle payments, processor disputes, supplier checks, access removal and tax filing. No external replies, refunds, account changes, listing updates or deployment were made from this folder.

Verification: **15 website tests passed**, using temporary databases, covering pricing, coupons, holidays, daily limits, concurrent retries, gift-card activation/restoration, private cancellation, customer privacy and protected exports. The live database integrity check passed and all 43 IDs were preserved. JavaScript syntax and the pickup-day display were also checked. Keep the backup and order-change log private; they contain customer information.
