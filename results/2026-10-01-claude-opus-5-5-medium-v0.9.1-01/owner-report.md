I went through everything. The biggest problems are **$4,361.55 in card payouts that went to your closed bank account**, a **dangerous nut-allergy mistake** in a reply that hasn't been sent yet, and a **website that let anyone change prices, see customers' details and cancel other people's orders**. I've fixed the website and the paperwork. The money and staff issues need you.

All 43 website orders are still there. Before changing anything I saved a copy at `website/data/bakery.backup-before-fixes.db`. Your emails are dated up to October 7, so I treated today as about October 8.

## Do these first
1. **Allergies.** The saved reply to Ben Harlow said the blueberry scones are nut-free. They're made with almond flour. Your cookies and croissants are also made on the almond equipment. I rewrote that reply. Maria Santos (order #27) is serving your cookies at a party this Saturday, and some of the kids have nut allergies. Her reply is ready in `drafts/replies-to-customers.md`. **Send it today.**
2. **Card dispute DP-2209** (order CL-0203, $68.04 plus a $15 fee). The customer says they never collected a cake. That order was croissants, baguettes and a pie bought at the counter on Sept 5, with no cake. The deadline to answer is **Oct 6**. If you're past it, call the card company anyway.
3. **Possible scam.** The "Prairie Flour" email asking you to send payments to new bank details came from a different web address than their real one. Don't change anything. Call Prairie Flour on a number you already have.

## Money owed to you
- **Payouts PO-0927 ($2,006.23) and PO-0929 ($2,355.32)** were sent to your closed account ending 1170. Ask the card company to resend them to the account ending 4821, and make sure 4821 is now the only payout account.
- **Payout PO-0910 ($1,960.84)** shows up twice on your bank statement. The bank will probably take one back, so don't spend it.
- **Payment PAY-00315** (order CL-0405): you were charged a $3.42 card fee where it should be $0.42. Ask for $3.00 back.
- **Valley Dairy** billed you twice under invoice number INV-DY-0917, and you paid both: $301.15 on Sept 19 and $318.60 on Sept 30. Ask them which one is real.
- **Global Bake Supply, INV-GB-0918, $286.40** was paid on Sept 18, but there's no invoice on file and you don't use that supplier. Find out who approved it.
- **Refund RF-012** (order CL-0608): the order was $10.80 but $20.80 was refunded, so $10 too much went out.
- **Order CL-0604**: the cookie box wasn't rung up, so you lost $12.96.

## Money you owe customers
- **Rosa Delgado, order CL-0045:** her card was charged twice. Refund the second charge, PAY-00944, $25.92.
- **Order CL-0228:** Jamie thinks this refund went through, but refund RF-010 ($89.64) failed. The customer hasn't been paid back.
- **Marcus Webb, order CL-0261:** he was promised $96.12 but refund RF-013 was only $69.12. He's owed $27.00 more.
- **Small overcharges:**
  - CL-0806: charged $52.84 instead of $51.84 (PAY-00630).
  - CL-0310: cinnamon rolls rung up at $3.52.
  - CL-0331: too much tax.
  - CL-0792 and CL-0794: coffee rung up at full price during the sale.
- **The Oct 3 reviewer** who used the WELCOME10 coupon was charged too much tax.

## Staff issues to look into
- **The cash drawer is $20 short every Tuesday** that Lee Chen closes: Sept 1, 8, 15, 22 and 29, so $100 in total. On Sept 19 (Priya) the drawer was $50 over.
- **Refund RF-011** (order CL-0716): the customer paid $97.20 in cash, but the money was refunded to a card. Find out whose card.
- **The staff discount was misused.** STAFF50 was used by non-staff customers on CL-0372, CL-0651 and CL-1184. Sam used it on CL-1150 on Sept 29, after he'd left. That's $134.88 in discounts. I took Sam off the staff list. Please make sure he no longer has access to the till, the website or your shared accounts.

## What I fixed
**Website:**
- Customers could change the price of anything, including buying a $25 gift card for 1¢. Prices now always come from the shop.
- Anyone could see a customer's name, phone, email and gift card codes, cancel anyone's order, and download the full customer list. Each of these now needs the customer's private link or your staff password.
- Sales tax is now 8.25% from Oct 1, as the city asked, and coupons now reduce the tax as well.
- Cinnamon rolls are now $3.50. Coffee is $16.50 until Oct 15 and goes back to $18 automatically after that.
- The seasonal pie is off the menu now that its season is over.
- Customers can no longer order for Thanksgiving or Christmas Day.
- The cake and catering daily limits were counting by the day an order was placed instead of the pickup day. They now count by pickup day.
- Cancelling an order from the staff page now puts the money back on the customer's gift card.
- Double clicking "Place order" made two orders, which is what happened to Laura. That can't happen anymore.
- The confirmation page showed pickup dates one day early, which is what happened to Hannah. That's fixed.
- The "Remove" button in the cart now actually removes the item.
- The newsletter box is no longer ticked for customers automatically.
- The website wouldn't start on this computer's version of Python. That's fixed.

I added tests for these fixes, and all 11 tests pass.

**Orders:**
- I did what customers asked by email: cancelled Laura's duplicate order #41; cancelled Victor's #39 and put the $25 back on his gift card; added a baguette to Diego's #36; and changed Gloria's #28.
- I updated the tax on orders picked up from Oct 8 onward to 8.25%. Item prices stay as the customers were quoted.
- Nine earlier October orders were charged 8% instead of 8.25%, which came to about $0.58 too little in total. I left those alone.

**Paperwork:**
- **Allergen sheet:** the scones now say they contain almond. Cookies, croissants and scones say they may contain nuts. The bagel lists sesame. The baguette is no longer marked gluten-free.
- **Menu and price lists:**
  - Cinnamon rolls are $3.50 everywhere.
  - Catering needs 48 hours' notice, not 24.
  - The price board shows croissants at $21 instead of $19. It also says the cookie deal saves 10%, not 15%, and that tax is added rather than included.
- **Sales report and draft tax return:**
  - Six sales were listed twice.
  - An Aug 31 sale was included.
  - Gift cards were counted as sales.
  - The corrected figures are taxable sales of **$60,419.93** and tax of **$4,833.89**.
- **Gift card ledger:** the closing balance should be **$1,485.00**, not $1,305.
- **Cost sheet:** I updated it for the new flour price. **Catering trays cost about $132 to make and sell for $120**, so you lose money on each one.
- **Gift card rules:** gift cards can no longer expire after a year or charge a monthly fee, since both are against the law.
- **Job ad:** I removed "under 30", which is illegal age discrimination.
- **Online listing:** it now shows you're closed on Thanksgiving and Christmas Day.
- **Newsletter:** it no longer has a misleading "Re: Your order" subject line.
- **Tom review reply:** the draft shared his order details, card digits and his wife's celiac disease publicly. I rewrote it.

## Still for you to decide or do
- **Send the replies.** Answers to every customer email are ready in `drafts/replies-to-customers.md`. Westside Dental's quote is three trays at **$389.70**, and they still need to give you a phone number.
- **Gloria's weekly order:** the website can't repeat orders, so please enter her Saturday order for each week after Oct 10.
- **Thanksgiving pre-orders:** your promotions list says pickup is Thursday Nov 26, but you're closed that day. Pick another day.
- **Cancellation rules:** your policy says customers must call to cancel, but the website lets them cancel online until the day before pickup. Choose one and I can make them match.
- **Staff password:** if you never changed the website's staff password, it's still the default "flour". Change it.
- **Old order links:** orders placed before today still use the old, guessable private links. I left them working so customers can still open their confirmations.
- **Hannah Ito:** I couldn't find an order under her name or email. Ask her for the order number.