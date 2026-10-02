# Corner Loaf Bakery: what I found and what to do

There are several separate problems, rather than one cause: money not reaching your bank, customer refunds needing attention, incorrect food allergy claims, ordering bugs, and reports that count some sales twice. Catering also costs more to make than you charge.

I corrected the supplied website and shop documents. All **43 existing orders** and their **71 item records**, agreed amounts, confirmation links, three gift-card balances and three recorded payments are preserved. The database passed its integrity check. A complete before-change database is in `review/backups/bakery-before-review.db`. Original books and edited shop documents are backed up too. Keep this folder private: it contains customer information.

These are local file changes. The public website, actual register, printed materials and external listing still need to be updated from them. No money was moved, tax return filed, email sent or review posted.

## Do these first

1. **Correct allergy advice before accepting allergy orders.** Scones contain almond flour. Cookies and croissants share almond equipment; cookies also contain soy. Cinnamon rolls contain milk and butter. Bagels contain sesame. Baguettes are not gluten-free. The ingredient sheet and website now say this correctly. Send Ben Harlow the corrected draft. For the supplied Oct 6 message, contact Maria Santos about **order #27**, two cookie boxes for a children's party with tree nut allergies, before baking or collection. Do not tell her the cookies are safe for those children. Catering fillings need their own ingredient checks.
2. **Trace $4,361.55 missing from your current account.** **PO-0927: $2,006.23** and **PO-0929: $2,355.32** went to the closed account ending **1170**. Neither appears in the bank statement for the current account ending **4821**. Ask the processor and bank where the funds are and have them reissued if returned. Verify the destination for future payouts.
3. **Resolve customer charges and promised refunds.** **CL-0045 / PAY-00031 and PAY-00944** has two $25.92 captured payments for one sale. **CL-0228 / RF-010** is a failed $89.64 refund, despite Jamie's email saying it was done. **CL-0261 / RF-013** refunded $69.12 after a full $96.12 refund was promised: **$27 remains**. Before issuing money, check the current processor record so you do not duplicate a later correction. Rosa and Marcus's email identities differ from the register emails; match their receipts/payment details privately.
4. **Respond to dispute DP-2209 by October 6.** It concerns **CL-0203, $68.04**, with a possible **$15 fee**. The dispute says a cake was not collected, but the register shows croissants, baguettes and pie. Verify the actual charge and gather genuine pickup evidence. If the supplied folder is being used after October 6, check the dispute's current outcome immediately.
5. **Do not adopt the bank details in the supplied Oct 5 flour email without verification.** The sender domain differs from the established supplier domain. Call Prairie Flour using a contact you already trust. This may be impersonation; it is not proof of a real bank change.

## Other money problems, with the references to check

| What needs checking | Reference | Amount and action |
|---|---|---|
| Card charge exceeds order | CL-0806 / PAY-00630 | $52.84 captured versus $51.84 order: check and return the $1 excess if confirmed. |
| Processor fee exceeds contract | CL-0405 / PAY-00315 / PO-0910 | Fee $3.42 on a $4.05 charge should be $0.42 at 2.9% + 30¢. Ask for a $3 credit. |
| Refund exceeds original sale | CL-0608 / RF-012 | $20.80 refund against $10.80 sale: investigate $10 excess. Do not automatically charge the customer again. |
| Refund uses different tender | CL-0716 / RF-011 | Sale was cash; $97.20 refund says card. Confirm recipient and whether a cash refund was also made. |
| Incorrect September tax | CL-0331 | $15 sale taxed $1.50 instead of $1.20. Check and correct the 30¢ excess. |
| Coffee promotion missed | CL-0792 and CL-0794 | Each charged $18 instead of $16.50 on Sept 20. Excess including tax is $1.62 each. |
| Staff discounts to ineligible people | CL-0372, CL-0651, CL-1150, CL-1184 | Discounts total $134.88. Three emails are nonstaff; Sam used his after leaving Sept 15. Check authorization and restrict register access. |
| Cash shortages and overage | Sept 1, 8, 15, 22, 29; Sept 19 | Five $20 shortages signed by Lee total $100; one $50 overage signed by Priya makes a $50 net shortage. Deposits match counted cash. Review counting/change/float procedures; this does not establish theft. |
| Duplicate bank entry | PO-0910, Sept 10 | Same $1,960.84 bank row appears twice; only one processor payout. Verify bank transaction IDs before counting twice or deleting a real entry. |
| Supplier invoice number reused | INV-DY-0917 | Sept 17 invoice $301.15 and Sept 29 invoice $318.60 both have bank debits. Obtain both invoices and correct the reference; different amounts are not enough to assume a duplicate payment. |
| Bank payment has no supplied invoice | INV-GB-0918, Global Bake Supply | $286.40 debit Sept 18: obtain invoice and verify purpose/vendor. |

Every supplied payout agrees with the captured payments less recorded fees and succeeded refunds when grouped by settlement date. That arithmetic does not resolve the exceptional charges/refunds above, or prove that missing payouts reached your bank. The failed refund is not included as money returned.

## September's books

I left the original register exports, bank statement, payment/refund records, sales report and draft tax return intact as evidence. The corrected working copies are in `review/`:

- Six identical sales rows were repeated: **CL-0316, CL-0534, CL-0742, CL-0845, CL-1016, CL-1177**. Their pretax value is **$315.75**. The August 31 transaction **CL-0831-0107**, $90 before tax/$97.20 total, also belongs outside September.
- After removing those rows, there are **1,216 unique September orders**, **$61,418.06** before discounts, **$200.38** discounts, **$61,217.68** sales after discounts and **$4,897.71** recorded sales tax.
- The old sales report's **$62,048.43** net sales includes the repeated/August sales and **$425 gift cards sold**. Selling a gift card creates an obligation to supply goods later; it is not immediately another bakery sale.
- Recorded succeeded refunds total **$871.57 including tax**. If those are treated as 8%-taxable refunds, the pretax portion is **$807.01** and tax portion **$64.56**. This gives provisional net sales of **$60,410.67** and recorded tax after refunds of **$4,833.15**.
- **Do not file the original draft or treat these provisional figures as final.** The draft's $60,346.11 taxable-sales line subtracts whole refunds, including tax. Its $4,779.31 tax line is $53.84 below the provisional recorded net tax. Your bookkeeper must resolve the excess refund, wrong tender, excess tax, promised refunds and gift-card redemption coverage before finalizing the return. September uses **8%**, not October's **8.25%**.
- The gift-card ledger's closing balance was an arithmetic error. I corrected it from **$1,305 to $1,485**: $1,240 opening + $425 sold − $180 redeemed. The register exports do not separately identify those gift-card redemptions; match the $180 to actual sales before adding any income or tax again.

See `september-sales-reconciled.csv`, `sales-tax-review.csv`, `register-issues.csv` and `money-actions.csv` for the working figures and exact references.

## What I fixed in the website

- New orders charge **8.25% tax from October 1**, after coupon discounts. Gift-card purchases remain untaxed and undiscounted. Customer-submitted prices cannot override shop prices.
- Cinnamon rolls now cost **$3.50** for new October orders. Coffee beans are correctly identified as **12 oz (340 g)** and return from $16.50 to $18 after October 15.
- Checkout prevents repeated clicks from creating duplicate orders and sends the same request reference when retrying an interrupted submission. Removing an item really removes it from the saved cart. Old cart prices refresh from the shop catalog.
- Pickup dates no longer shift to the previous day on confirmations. Store time uses Springfield's Central time. Thanksgiving and Christmas are blocked, catering/cakes require 48 hours, and production limits count the **pickup day**, not the order-placement day.
- Customer details and gift-card codes no longer appear without a private confirmation link. The orders download now needs staff login. New private links use random secrets. Existing links still work.
- Cancellation requires the customer's private link and 48 hours' notice. Paid orders require staff help. Staff cancellation restores redeemed gift credit once and voids unused gift cards bought by the order. A used purchased gift card requires staff resolution.
- Newly purchased gift cards cannot be spent until staff record payment. Staff now have payment/cancellation buttons; only click “Payment received” after actually collecting payment. Paid/cancelled orders show no money still to collect. Cancelling does **not** automatically issue card or cash refunds; staff must handle those separately.
- Newsletter signup now starts unticked. Customer-entered errors display as text, exported spreadsheet cells cannot run customer-entered formulas, and checkout fields have useful labels.

The final tests cover normal ordering, prices, coupon tax, effective dates, concurrent first-order coupons, repeated submissions, holiday/notice rules, capacity, customer privacy, staff login, gift-card activation/restoration/voiding and paid/cancelled balances. They use temporary databases, never the real order database.

## Shop documents and customer requests

I aligned the menu, website/register price files and board with $3.50 cinnamon rolls and $21 croissant boxes. The two-cookie-box offer saves **10%, not 15%**. The board now says prices are before tax. The menu now requires 48 hours for catering. The allergy sheet, door-sign holiday text and local listing holiday closures are corrected; existing phone, website, regular hours and pickup-only service were already consistent.

Gift-card terms now have no expiration or inactivity fees and match the 14-day unused-card refund policy. Receipt text includes the custom-cake/catering exception. Cancellation policy matches the site. Confirm applicable Illinois cash-redemption requirements before using the final gift-card terms. Sam is recorded as former staff and removed from the current discount list. The job posting no longer excludes applicants over 30. The Thanksgiving pickup promotion is on hold because it advertised collection on a closed day; choose an open day and confirm dinner-roll availability before advertising.

I replaced Ben's unsafe allergy reply and Tom's public reply that exposed customer/contact/payment/health details and claimed unverified facts. The newsletter now has an appropriate subject and accurate cinnamon-roll price. Add a working unsubscribe link and postal address, and verify consent for signups from the previously prechecked box before sending. Existing subscriber records remain intact.

The environment says **October 1**, but supplied messages extend to **October 7**. I did not apply those later customer requests to real orders. `customer-actions.md` gives the current and requested details so you can verify dates and act:

| Customer / order | Next action |
|---|---|
| Laura #40/#41 | Keep #40 and cancel verified duplicate #41; each currently records $24.30. |
| Victor #39 | Cancel verified request and restore $25 to the card from paid gift purchase #38. |
| Diego #36 | Add a baguette after verification; proposed $15.16 total at October tax. |
| Gloria #28 | Requested three sourdoughs and one croissant box: proposed $51.96 total. Only a one-off order exists; arrange future Saturdays separately. |
| Nina #30 | Recorded balance is $26.84 after $25 gift credit. New-rate tax would make it $26.96; agree treatment before changing the confirmation. |
| Tessa #34 | Recorded cash balance $22.68; new-rate total would be $22.73. Confirm treatment before quoting a changed amount. |
| Hannah, no matching record | Ask privately for order number/confirmation link; do not guess which order was hers. |
| Maria #27 / Jordan / Ben | Give the corrected allergy information and resolve any affected purchase before production. |
| Westside Dental, not booked | Three trays serve about 30–36. Listed price with October tax $389.70. Check phone, fillings, pickup capacity and catering price before confirming. |

Existing October orders still have their original 8% amounts and old cinnamon-roll unit prices where applicable. I have not increased amounts already agreed with customers. `existing-order-price-review.csv` lists tax-only comparisons for each food order for your bookkeeper. Decide whether to absorb or agree corrections; do not silently charge a different amount.

## Catering is losing money

Flour rose from $10.30 to $12.875 per 25 kg bag on September 15, or **$0.412 to $0.515/kg**. I updated the current cost sheet. It is not a restatement of early September costs.

A catering tray now costs **$132.19 in ingredients and labor**, against a **$120 price**: a **$12.19 loss per tray before rent, utilities and other overhead**. Three trays lose about $36.56 before overhead. Review portions, labor or price before agreeing to Westside's request. A 25% margin on these listed direct costs alone would require roughly **$176.25 per tray**; that is a planning example, not a price change I made.

## Putting the fixes into use

Have whoever maintains your site publish the changed website files and the catalog-price update while preserving the current production database and any orders received since this folder was copied. **Do not overwrite a newer database with either supplied snapshot.** Set a strong private staff password (`ADMIN_PASSWORD`) and use HTTPS. The old default password is still retained for compatibility and must be changed before public use.

Load the corrected register prices and October tax rate into the actual POS; restrict staff discounts and revoke Sam's access to shop services. Replace printed menu/board/allergen/receipt/sign materials and update the external listing. QuickPrint cards need checking against the corrected copy before distribution. Owner decisions remain for catering prices, Thanksgiving pickup, the optional Oct 24 street fair and Nov 1 winter-market applications. October rent and dairy deliveries are confirmed; insurance auto-renews Nov 1. OldPOS cancellation is confirmed and no OldPOS September debit is present in the supplied bank statement.

The drafts are ready for your review, but you still need to send appropriate replies and make the verified order adjustments. The money checklist is ready to take to your processor, bank and bookkeeper.
