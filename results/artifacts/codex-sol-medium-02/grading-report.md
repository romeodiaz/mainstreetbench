# Independent grading report — task01-sol-medium-02

**Primary issue handling: 12/12. Secondary exact-key handling: 10/12.** All five deliverables exist, the checker passes, and all frozen hashes are unchanged. The submitted receipts are **$14,223.00**, which is **$27.00 above** the corrected key. The rendered headline is **$12,039.00 earned revenue**, using a separately disclosed gift-card policy. These financial departures are not hidden by the issue-handling score.

The secondary zeros are item 06 (literal coffee-product label differs from the keyed target, despite correct consolidation) and item 07 (all four incorrect totals retained with flags). The primary rule permits correct, ID-specific flagging. No additional weights or composite acceptance score were introduced.

## Scope, model and independence

Read first: protocol.md, reference/task-prompt.md, reference/answer-key.md and frozen-manifest.json. Evidence consists of those references and frozen files. Independent calculations start from frozen/original_customer_orders.csv; reference/generate.py was not needed or run. No submitted files were repaired or rewritten. No solver contact, prior run, prior report, reasoning transcript or benchmark-repository consultation occurred.

The preregistered solver is GPT-6.1 Sol / medium. Actual solver model/effort are unverified because turn_context is not part of the authorized evidence. The grader is instruction-identified as Codex based on GPT-6; exact deployed SKU and effort are unavailable. The requested different-model condition cannot be certified from this evidence. **Access audit: inconclusive.** The instruction not to read the solver transcript limits the protocol’s transcript-audit requirement; this report makes no certified-blind claim.

The cleaning log reports a start of September 30, 2026 at 17:52:57 America/Los_Angeles. The manifest freeze is September 30 at 17:57:36.715791, a 4m39.716s interval. This is a log-to-freeze interval, not independently verified execution duration. User interventions, actual completion time and enforcement of the 30-minute limit are unknown.

## Preregistered issue scores

| Item | Issue | Primary | Secondary |
| --- | --- | --- | --- |
| 01 | Name aliases | 1 | 1 |
| 02 | Name whitespace | 1 | 1 |
| 03 | Mixed dates | 1 | 1 |
| 04 | Numeric prices/totals | 1 | 1 |
| 05 | Email recovery and missing email flags | 1 | 1 |
| 06 | Product normalization | 1 | 0 |
| 07 | Arithmetic mismatches | 1 | 0 |
| 08 | Phone formatting | 1 | 1 |
| 09 | Refunds | 1 | 1 |
| 10 | Future dates | 1 | 1 |
| 11 | Test records | 1 | 1 |
| 12 | Exact duplicates | 1 | 1 |

Evidence conventions: source lines refer to frozen/original_customer_orders.csv; clean lines refer to frozen/output/clean_orders.csv; header is line 1. Log references refer to frozen/output/cleaning_log.md. Each JSON issue includes all affected IDs, before/after fields, source lines, clean line, and ID-specific log lines. The date/phone appendix below covers all 293 retained IDs, including every duplicate source occurrence.

### 01 — Name aliases: primary 1/1, secondary 1/1

All nine affected order IDs resolve to Maria Lopez, James Chen or Priya Patel using matching phone and corroborating observed email. Missing emails on 10146, 10191 and 10052 are recovered from the same contact groups. All 64 contact groups remain separate; no false merge or split was found.

| Order ID | Source line(s) | Clean line | Source evidence | Submitted result |
| --- | --- | --- | --- | --- |
| 10032 | 251 | 33 | Customer Name='maria lopez'; Email='maria.lopez@example.com'; Phone='(555) 745-0100' | customer_name='Maria Lopez'; customer_id='C-73fadad9de66'; email='maria.lopez@example.com'; phone='(555) 745-0100' |
| 10213 | 271 | 214 | Customer Name='M. Lopez'; Email='maria.lopez@example.com'; Phone='+1 555 745 0100' | customer_name='Maria Lopez'; customer_id='C-73fadad9de66'; email='maria.lopez@example.com'; phone='(555) 745-0100' |
| 10146 | 272 | 147 | Customer Name='Lopez, Maria'; Email=''; Phone='(555) 745-0100' | customer_name='Maria Lopez'; customer_id='C-73fadad9de66'; email='maria.lopez@example.com'; phone='(555) 745-0100' |
| 10223 | 130 | 224 | Customer Name='MARIA LOPEZ'; Email='maria.lopez@example.com'; Phone='(555) 745-0100' | customer_name='Maria Lopez'; customer_id='C-73fadad9de66'; email='maria.lopez@example.com'; phone='(555) 745-0100' |
| 10208 | 290 | 209 | Customer Name='james chen'; Email='james.chen@example.com'; Phone='555-829-0101' | customer_name='James Chen'; customer_id='C-31525888ad14'; email='james.chen@example.com'; phone='(555) 829-0101' |
| 10040 | 298 | 41 | Customer Name='J. Chen'; Email='james.chen@example.com'; Phone='(555) 829-0101' | customer_name='James Chen'; customer_id='C-31525888ad14'; email='james.chen@example.com'; phone='(555) 829-0101' |
| 10191 | 48,56 | 192 | Customer Name='Chen, James'; Email=''; Phone='555.829.0101' | customer_name='James Chen'; customer_id='C-31525888ad14'; email='james.chen@example.com'; phone='(555) 829-0101' |
| 10052 | 177,260 | 53 | Customer Name='priya patel'; Email=''; Phone='(555) 151-0102' | customer_name='Priya Patel'; customer_id='C-6e8fc6022d02'; email='priya.patel@example.com'; phone='(555) 151-0102' |
| 10038 | 201 | 39 | Customer Name='P. Patel'; Email='priya.patel@example.com'; Phone='555-151-0102' | customer_name='Priya Patel'; customer_id='C-6e8fc6022d02'; email='priya.patel@example.com'; phone='(555) 151-0102' |

### 02 — Name whitespace: primary 1/1, secondary 1/1

All eight listed IDs have trimmed/collapsed names, including the doubled internal space in James Chen. Whitespace normalization agrees with the independently normalized source.

| Order ID | Source line(s) | Clean line | Source evidence | Submitted result |
| --- | --- | --- | --- | --- |
| 10248 | 160 | 249 | Customer Name='Marcus Haddad  ' | customer_name='Marcus Haddad' |
| 10224 | 264 | 225 | Customer Name='James  Chen' | customer_name='James Chen' |
| 10111 | 236 | 112 | Customer Name='  Maria Lopez' | customer_name='Maria Lopez' |
| 10243 | 291 | 244 | Customer Name='  Tariq Rahman' | customer_name='Tariq Rahman' |
| 10119 | 207 | 120 | Customer Name='Luis Novak  ' | customer_name='Luis Novak' |
| 10023 | 246 | 24 | Customer Name='Yara Weber  ' | customer_name='Yara Weber' |
| 10125 | 86,121 | 126 | Customer Name='  Jade Garcia' | customer_name='Jade Garcia' |
| 10259 | 240 | 260 | Customer Name='  Elena Evans' | customer_name='Elena Evans' |

### 03 — Mixed dates: primary 1/1, secondary 1/1

All 293 retained dates were independently parsed using the five observed source formats and compared with output dates. All are canonical YYYY-MM-DD and agree, including the two explicitly logged year corrections. The three excluded tests and four duplicate copies are covered in items 11 and 12.

All retained order IDs 10001–10293 are covered in the combined appendix. Every row comparison passed.

### 04 — Numeric prices/totals: primary 1/1, secondary 1/1

All 25 affected unit prices and both affected totals are plain decimal literals equal to the source numeric values after removing currency decorations. This formatting pass does not imply arithmetic correctness; item 07 covers that separately.

| Order ID | Source line(s) | Clean line | Source evidence | Submitted result |
| --- | --- | --- | --- | --- |
| 10036 | 161 | 37 | Unit Price='21.00 USD'; Total='84.00' | unit_price='21.00'; recorded_total='84.00' |
| 10235 | 36 | 236 | Unit Price='$25.00'; Total='25.00' | unit_price='25.00'; recorded_total='25.00' |
| 10080 | 295 | 81 | Unit Price='$ 9.00'; Total='27.00' | unit_price='9.00'; recorded_total='27.00' |
| 10141 | 166 | 142 | Unit Price='9.00 USD'; Total='18.00' | unit_price='9.00'; recorded_total='18.00' |
| 10233 | 249 | 234 | Unit Price='$ 48.00'; Total='48.00' | unit_price='48.00'; recorded_total='48.00' |
| 10051 | 286 | 52 | Unit Price='$18.00'; Total='72.00' | unit_price='18.00'; recorded_total='72.00' |
| 10182 | 114 | 183 | Unit Price='$21.00'; Total='84.00' | unit_price='21.00'; recorded_total='84.00' |
| 10262 | 122 | 263 | Unit Price='9.00 USD'; Total='18.00' | unit_price='9.00'; recorded_total='18.00' |
| 10175 | 144 | 176 | Unit Price='$ 18.00'; Total='72.00' | unit_price='18.00'; recorded_total='72.00' |
| 10195 | 252 | 196 | Unit Price='$ 9.00'; Total='36.00' | unit_price='9.00'; recorded_total='36.00' |
| 10230 | 137 | 231 | Unit Price='48.00 USD'; Total='48.00' | unit_price='48.00'; recorded_total='48.00' |
| 10009 | 289 | 10 | Unit Price='$ 21.00'; Total='21.00' | unit_price='21.00'; recorded_total='21.00' |
| 10027 | 277 | 28 | Unit Price='$9.00'; Total='18.00' | unit_price='9.00'; recorded_total='18.00' |
| 10187 | 46 | 188 | Unit Price='$21.00'; Total='42.00' | unit_price='21.00'; recorded_total='42.00' |
| 10171 | 157 | 172 | Unit Price='$9.00'; Total='18.00' | unit_price='9.00'; recorded_total='18.00' |
| 10130 | 187 | 131 | Unit Price='$ 18.00'; Total='54.00' | unit_price='18.00'; recorded_total='54.00' |
| 10217 | 229 | 218 | Unit Price='$ 9.00'; Total='36.00' | unit_price='9.00'; recorded_total='36.00' |
| 10073 | 49 | 74 | Unit Price='$ 48.00'; Total='48.00' | unit_price='48.00'; recorded_total='48.00' |
| 10103 | 266 | 104 | Unit Price='$ 18.00'; Total='18.00' | unit_price='18.00'; recorded_total='18.00' |
| 10120 | 23 | 121 | Unit Price='$21.00'; Total='21.00' | unit_price='21.00'; recorded_total='21.00' |
| 10286 | 119 | 287 | Unit Price='$9.00'; Total='18.00' | unit_price='9.00'; recorded_total='18.00' |
| 10077 | 228 | 78 | Unit Price='$ 21.00'; Total='21.00' | unit_price='21.00'; recorded_total='21.00' |
| 10129 | 238 | 130 | Unit Price='48.00 USD'; Total='48.00' | unit_price='48.00'; recorded_total='48.00' |
| 10256 | 147 | 257 | Unit Price='$ 25.00'; Total='100.00' | unit_price='25.00'; recorded_total='100.00' |
| 10041 | 154 | 42 | Unit Price='$ 21.00'; Total='84.00' | unit_price='21.00'; recorded_total='84.00' |
| 10031 | 205 | 32 | Unit Price='120.00'; Total='$120.00' | unit_price='120.00'; recorded_total='120.00' |
| 10181 | 156 | 182 | Unit Price='120.00'; Total='$120.00' | unit_price='120.00'; recorded_total='120.00' |

### 05 — Email recovery and missing email flags: primary 1/1, secondary 1/1

The eight actually recoverable emails in the key are recovered from the sole observed email in each matching phone group. The six unrecoverable rows, including errata IDs 10058 and 10215, remain blank and are specifically flagged in cleaning_log.md:943–948. A CSV flags field is not required when the log correctly flags the IDs. No address was invented.

| Order ID | Source line(s) | Clean line | Source evidence | Submitted result |
| --- | --- | --- | --- | --- |
| 10271 | 265 | 272 | Email=''; Phone='(555) 404-0118' | email='owen.qureshi@example.com'; flags='' |
| 10183 | 12 | 184 | Email=''; Phone='555-141-0112' | email='arjun.park@example.com'; flags='' |
| 10127 | 212 | 128 | Email=''; Phone='555.729.0141' | email='diego.stein@example.com'; flags='' |
| 10113 | 220 | 114 | Email=''; Phone='+1 555 522 0120' | email='lena.park@example.com'; flags='' |
| 10069 | 218 | 70 | Email=''; Phone='555.707.0126' | email='daniel.price@example.com'; flags='' |
| 10058 | 253 | 59 | Email=''; Phone='5553610157' | email=''; flags='' |
| 10215 | 9 | 216 | Email=''; Phone='555.371.0113' | email=''; flags='' |
| 10047 | 193 | 48 | Email=''; Phone='(555) 720-0159' | email='samuel.farouk@example.com'; flags='' |
| 10110 | 13 | 111 | Email=''; Phone='5556220136' | email='mei.rahman@example.com'; flags='' |
| 10254 | 244 | 255 | Email=''; Phone='+1 555 916 0130' | email='theo.holm@example.com'; flags='' |
| 10063 | 102 | 64 | Email=''; Phone='555.888.0110' | email=''; flags='' |
| 10095 | 178 | 96 | Email=''; Phone='555.888.0110' | email=''; flags='' |
| 10222 | 40 | 223 | Email=''; Phone='+1 555 862 0111' | email=''; flags='' |
| 10248 | 160 | 249 | Email=''; Phone='(555) 862-0111' | email=''; flags='' |

### 06 — Product normalization: primary 1/1, secondary 0/1

All nine affected rows are consolidated into the correct product groups, so primary handling passes. For the strict exact-key secondary score, 10136, 10051 and 10045 use Coffee Beans 1 lb rather than the key target Coffee Beans 1lb. This is a canonical-label spelling departure only: all coffee rows share the same submitted label, and no units or receipts are split. Secondary is zero under a literal reading of exact answer-key handling.

| Order ID | Source line(s) | Clean line | Source evidence | Submitted result |
| --- | --- | --- | --- | --- |
| 10001 | 44 | 2 | Product='Sourdogh Loaf' | product='Sourdough Loaf' |
| 10289 | 109 | 290 | Product='sourdough loaf' | product='Sourdough Loaf' |
| 10112 | 216 | 113 | Product='Sourdogh Loaf' | product='Sourdough Loaf' |
| 10122 | 50 | 123 | Product='Croissant Box 6' | product='Croissant Box (6)' |
| 10078 | 28 | 79 | Product='croissant box (6)' | product='Croissant Box (6)' |
| 10011 | 199 | 12 | Product='Croissant Box 6' | product='Croissant Box (6)' |
| 10136 | 4 | 137 | Product='Coffee Beans 1 lb' | product='Coffee Beans 1 lb' |
| 10051 | 286 | 52 | Product='Cofee Beans 1lb' | product='Coffee Beans 1 lb' |
| 10045 | 124 | 46 | Product='Coffee Beans 1 lb' | product='Coffee Beans 1 lb' |

### 07 — Arithmetic mismatches: primary 1/1, secondary 0/1

All four arithmetic differences are explicitly identified in CSV flags and cleaning_log.md:570–573, including the correct quantity-times-price alternatives. That satisfies primary flagging/no-invention handling. Secondary is zero because recorded totals remain 54.00, 4.50, 22.50 and 109.00 instead of the required 27.00, 9.00, 27.00 and 100.00. The log is consistent with this decision.

| Order ID | Source line(s) | Clean line | Source evidence | Submitted result |
| --- | --- | --- | --- | --- |
| 10277 | 35 | 278 | Qty='3'; Unit Price='9.00'; Total='54.00' | quantity='3'; unit_price='9.00'; recorded_total='54.00'; net_revenue='54.00'; gift_card_proceeds='0.00'; flags='total_differs_from_quantity_times_price' |
| 10030 | 250 | 31 | Qty='1'; Unit Price='9.00'; Total='4.50' | quantity='1'; unit_price='9.00'; recorded_total='4.50'; net_revenue='4.50'; gift_card_proceeds='0.00'; flags='total_differs_from_quantity_times_price' |
| 10239 | 259 | 240 | Qty='3'; Unit Price='9.00'; Total='22.50' | quantity='3'; unit_price='9.00'; recorded_total='22.50'; net_revenue='22.50'; gift_card_proceeds='0.00'; flags='total_differs_from_quantity_times_price' |
| 10240 | 151 | 241 | Qty='4'; Unit Price='25.00'; Total='109.00' | quantity='4'; unit_price='25.00'; recorded_total='109.00'; net_revenue='0.00'; gift_card_proceeds='109.00'; flags='total_differs_from_quantity_times_price' |

### 08 — Phone formatting: primary 1/1, secondary 1/1

Every retained row and every customer row has a (555) NNN-NNNN phone. Independent digit normalization, including optional leading US country code, agrees with the source for every retained order. The phone-derived customer IDs are stable for this snapshot, with no collisions.

All retained order IDs 10001–10293 are covered in the combined appendix. Every row comparison passed.

### 09 — Refunds: primary 1/1, secondary 1/1

All three refunds are retained once with negative quantities and negative recorded receipts: 10048 −25.00, 10070 −27.00, 10211 −27.00, totaling −79.00. References to original sales are correct. Gift-card refund 10048 reduces gift_card_proceeds rather than the submitted earned-revenue column; it still reduces the reference-comparable receipts metric. The accounting-column difference is disclosed separately and is not a dropped refund.

| Order ID | Source line(s) | Clean line | Source evidence | Submitted result |
| --- | --- | --- | --- | --- |
| 10048 | 222 | 49 | Qty='-1'; Total='-25.00'; Notes='refund for #10043' | quantity='-1'; recorded_total='-25.00'; net_revenue='0.00'; gift_card_proceeds='-25.00'; refund_for_order_id='10043' |
| 10070 | 200 | 71 | Qty='-3'; Total='-27.00'; Notes='refund for #10067' | quantity='-3'; recorded_total='-27.00'; net_revenue='-27.00'; gift_card_proceeds='0.00'; refund_for_order_id='10067' |
| 10211 | 261 | 212 | Qty='-3'; Total='-27.00'; Notes='refund for #10209' | quantity='-3'; recorded_total='-27.00'; net_revenue='-27.00'; gift_card_proceeds='0.00'; refund_for_order_id='10209' |

### 10 — Future dates: primary 1/1, secondary 1/1

Both impossible future dates are corrected to the exact keyed dates, 10221 to 2026-06-04 and 10269 to 2026-08-06, and marked year_corrected_from_62. cleaning_log.md:584–585 gives source dates and supporting adjacent-order evidence. Both primary and secondary pass.

| Order ID | Source line(s) | Clean line | Source evidence | Submitted result |
| --- | --- | --- | --- | --- |
| 10221 | 83 | 222 | Order Date='6/4/62' | order_date='2026-06-04'; flags='year_corrected_from_62' |
| 10269 | 184 | 270 | Order Date='2062-08-06' | order_date='2026-08-06'; flags='year_corrected_from_62' |

### 11 — Test records: primary 1/1, secondary 1/1

All three keyed test IDs are absent from clean_orders.csv and customer rollups. The log explicitly excludes 90001 and 90002 and quarantines 90003 with its full original record and reasons. Qualified treatment of 90003 does not leave it in sales; exact exclusion handling passes.

| Order ID | Source line(s) | Clean line | Source evidence | Submitted result |
| --- | --- | --- | --- | --- |
| 90001 | 185 | absent | Customer Name='Test Customer'; Total='9.00'; Notes='test - ignore' | excluded |
| 90002 | 139 | absent | Customer Name='TEST'; Total='9.00'; Notes='testing checkout' | excluded |
| 90003 | 283 | absent | Customer Name='asdf'; Total='0.00'; Notes='' | excluded |

### 12 — Exact duplicates: primary 1/1, secondary 1/1

Each keyed duplicate occurs twice identically in the source and once in clean_orders.csv. The log records the removed and retained source lines for all four pairs. No real transaction was lost.

| Order ID | Source line(s) | Clean line | Source evidence | Submitted result |
| --- | --- | --- | --- | --- |
| 10125 | 86,121 | 126 | 2 identical rows | order_id='10125'; source_row='86' |
| 10282 | 158,171 | 283 | 2 identical rows | order_id='10282'; source_row='158' |
| 10052 | 177,260 | 53 | 2 identical rows | order_id='10052'; source_row='177' |
| 10191 | 48,56 | 192 | 2 identical rows | order_id='10191'; source_row='48' |

## Financial reconciliation

All calculations use exact decimal arithmetic. For the reference receipts metric, keep gift-card receipts and all refunds, remove the three tests and four duplicate copies, correct the two dates, and use quantity × unit price. This independently reproduces every full-data monthly value, top-ten amount, product total and inactive customer in the corrected key.

| Measure | Corrected reference | Submission | Assessment |
| --- | --- | --- | --- |
| Source rows | 300 | 300 | preserved |
| Retained transactions | 293 | 293 | match |
| Positive purchase rows | 290 | 290 | match |
| Refund rows | 3 | 3 | match; −$79.00 receipts |
| Real customers | 64 | 64 | match; no false merges or splits |
| Inactive customers | 32 | 32 | all names and last dates match |
| Full-data net receipts | $14,196.00 | $14,223.00 | over by $27.00 |
| Net gift-card receipts | $2,175.00 | $2,184.00 | over by $9.00 |
| Non-gift receipts | $12,021.00 | $12,039.00 | over by $18.00 |
| Future rows excluded: transactions | 291 | 291 | comparison variant only |
| Future rows excluded: receipts | $14,075.00 | $14,102.00 | over by $27.00 |

The submission actually retains both date-corrected rows. The excluded variant is independently reported only for comparison: remove 10221 ($100 gift card) and 10269 ($21 croissants), totaling $121.00. Correct excluded receipts are $14,075.00; the key’s $14,175.00 alternative is a typo. Customer and inactive counts remain 64 and 32.

The dashboard and customers.csv use earned revenue, excluding gift-card issuance, and count only positive purchases as orders. Those conventions are explicit. The task’s wording about what the bakery earned leaves an accounting ambiguity, but the protocol fixes receipts for key comparison. No redemption or settlement amounts are invented. The reference-comparable receipt totals here always include gift-card transactions.

| Order | Customer | Month | Key total | Recorded total | Recorded − key |
| --- | --- | --- | --- | --- | --- |
| 10277 | Owen Qureshi | 2026-08 | $27.00 | $54.00 | $27.00 |
| 10240 | Keiko Doyle | 2026-06 | $100.00 | $109.00 | $9.00 |
| 10030 | Ivy Rahman | 2025-10 | $9.00 | $4.50 | $-4.50 |
| 10239 | Lena Park | 2026-06 | $27.00 | $22.50 | $-4.50 |

### Every month

| Month | Key receipts | Submitted receipts | Receipt difference | Rendered earned revenue | Key receipts if future rows excluded | Submitted receipts if excluded |
| --- | --- | --- | --- | --- | --- | --- |
| 2025-10 | $1,914.00 | $1,909.50 | $-4.50 | $1,759.50 | $1,914.00 | $1,909.50 |
| 2025-11 | $1,915.00 | $1,915.00 | $0.00 | $1,815.00 | $1,915.00 | $1,915.00 |
| 2025-12 | $1,297.00 | $1,297.00 | $0.00 | $1,047.00 | $1,297.00 | $1,297.00 |
| 2026-01 | $1,179.00 | $1,179.00 | $0.00 | $1,029.00 | $1,179.00 | $1,179.00 |
| 2026-02 | $1,046.00 | $1,046.00 | $0.00 | $921.00 | $1,046.00 | $1,046.00 |
| 2026-03 | $1,176.00 | $1,176.00 | $0.00 | $1,176.00 | $1,176.00 | $1,176.00 |
| 2026-04 | $1,066.00 | $1,066.00 | $0.00 | $816.00 | $1,066.00 | $1,066.00 |
| 2026-05 | $579.00 | $579.00 | $0.00 | $504.00 | $579.00 | $579.00 |
| 2026-06 | $1,395.00 | $1,399.50 | $4.50 | $940.50 | $1,295.00 | $1,299.50 |
| 2026-07 | $1,466.00 | $1,466.00 | $0.00 | $1,041.00 | $1,466.00 | $1,466.00 |
| 2026-08 | $761.00 | $788.00 | $27.00 | $588.00 | $740.00 | $767.00 |
| 2026-09 | $402.00 | $402.00 | $0.00 | $402.00 | $402.00 | $402.00 |

Nine of twelve submitted receipt months match the key. October, June and August differ by −$4.50, +$4.50 and +$27.00 respectively. Only March and September rendered earned-revenue months equal the key receipts by value; the other ten also reflect gift-card exclusions.

### Top ten customers

| Reference rank | Customer | Key receipts | Submitted receipts | Submitted earned revenue | Rendered rank |
| --- | --- | --- | --- | --- | --- |
| 1 | Maria Lopez | $834.00 | $834.00 | $759.00 | 1 |
| 2 | Daniel Price | $697.00 | $697.00 | $597.00 | 2 |
| 3 | Tessa Park | $659.00 | $659.00 | $534.00 | 3 |
| 4 | Lena Park | $549.00 | $544.50 | $319.50 | outside top 10 |
| 5 | Ahmed Ali | $538.00 | $538.00 | $438.00 | 5 |
| 6 | Tariq Levi | $495.00 | $495.00 | $495.00 | 4 |
| 7 | Lily Russo | $494.00 | $494.00 | $369.00 | 8 |
| 8 | James Chen | $455.00 | $455.00 | $255.00 | outside top 10 |
| 9 | Diego Stein | $445.00 | $445.00 | $345.00 | 10 |
| 10 | Samuel Farouk | $435.00 | $435.00 | $435.00 | 6 |

The receipts-based top-ten membership and order match the key; only Lena Park’s receipt amount is $4.50 low. The rendered earned-revenue ranking differs as shown below; this is an accounting-definition effect, plus retained arithmetic differences.

| Rendered rank | Customer | Rendered earned revenue | Purchases | Last purchase |
| --- | --- | --- | --- | --- |
| 1 | Maria Lopez | $759.00 | 14 | 2026-07-24 |
| 2 | Daniel Price | $597.00 | 12 | 2026-09-23 |
| 3 | Tessa Park | $534.00 | 14 | 2026-07-28 |
| 4 | Tariq Levi | $495.00 | 12 | 2025-11-26 |
| 5 | Ahmed Ali | $438.00 | 8 | 2026-04-21 |
| 6 | Samuel Farouk | $435.00 | 11 | 2025-12-23 |
| 7 | Ivy Rahman | $379.50 | 9 | 2026-08-05 |
| 8 | Lily Russo | $369.00 | 9 | 2026-03-03 |
| 9 | Carlos Lopez | $354.00 | 7 | 2025-12-06 |
| 10 | Diego Stein | $345.00 | 8 | 2026-08-24 |

### Every product

| Reference product | Key net units | Submitted net units | Key receipts | Submitted receipts | Rendered treatment |
| --- | --- | --- | --- | --- | --- |
| Croissant Box (6) | 201 | 201 | $4,221.00 | $4,221.00 | $4,221.00 |
| Coffee Beans 1lb | 148 | 148 | $2,664.00 | $2,664.00 | Coffee Beans 1 lb label; $2,664.00 |
| Gift Card | 87 | 87 | $2,175.00 | $2,184.00 | Excluded from best-selling products; $2,184 proceeds in receipts section |
| Catering Tray | 18 | 18 | $2,160.00 | $2,160.00 | $2,160.00 |
| Sourdough Loaf | 208 | 208 | $1,872.00 | $1,890.00 | $1,890.00 |
| Birthday Cake | 23 | 23 | $1,104.00 | $1,104.00 | $1,104.00 |

All six net unit totals match. Sourdough receipts are $18.00 high and gift-card receipts $9.00 high. The other four receipt totals match. The dashboard shows five bakery products ranked by units, with gift cards omitted under its explicit policy.

### Every inactive customer

Inactivity is last purchase strictly before 2026-07-02 (more than 90 days as of 2026-09-30). All 32 names and dates below match the key and the rendered dashboard. No customer has a boundary-date ambiguity affecting this population. Refunds do not change the last-date/inactive results in this dataset.

| Customer | Reference last order / submitted last purchase | Match |
| --- | --- | --- |
| Gideon Petrov | 2025-11-13 | yes |
| Tariq Levi | 2025-11-26 | yes |
| Zara Lang | 2025-11-26 | yes |
| Carlos Lopez | 2025-12-06 | yes |
| Arjun Evans | 2025-12-08 | yes |
| Lena Reed | 2025-12-13 | yes |
| Nadia Stein | 2025-12-21 | yes |
| Samuel Farouk | 2025-12-23 | yes |
| Felix Price | 2026-01-06 | yes |
| Luis Novak | 2026-01-09 | yes |
| Mei Rahman | 2026-01-14 | yes |
| Owen Morgan | 2026-01-14 | yes |
| Owen Patel | 2026-01-16 | yes |
| Hannah Moreau | 2026-02-07 | yes |
| Elena Rahman | 2026-02-24 | yes |
| Jade Garcia | 2026-02-24 | yes |
| Lily Russo | 2026-03-03 | yes |
| Mei Ortiz | 2026-03-15 | yes |
| Omar Hart | 2026-03-20 | yes |
| Iris Grant | 2026-03-30 | yes |
| Ravi Russo | 2026-03-30 | yes |
| Elena Moreau | 2026-04-04 | yes |
| Alice Patel | 2026-04-10 | yes |
| Kwame Lang | 2026-04-17 | yes |
| Ahmed Ali | 2026-04-21 | yes |
| Hugo Stone | 2026-04-25 | yes |
| Daniel Nguyen | 2026-05-06 | yes |
| Mei Weber | 2026-05-28 | yes |
| Isaac Obi | 2026-05-30 | yes |
| Amara Holm | 2026-06-09 | yes |
| Ruth Fischer | 2026-06-19 | yes |
| Fatima Obi | 2026-06-21 | yes |

## Checker validity and artifact completion

Inspected check_dashboard.py in full before execution. It imports only standard-library modules and performs local reads and comparisons; no writes, subprocesses or networking. Ran once with Python -B against the frozen snapshot. Exit code 0: PASS; 290 HTML data-check values, 293 transactions, 64 customers, 32 inactive, $12,039 earned + $2,184 gift = $14,223 recorded receipts.

The checker meaningfully recalculates CSV aggregates, customer rollups, dates, refund links, duplicate/test coverage, static HTML cell text and chart widths. However, it deliberately requires original recorded totals and permits arithmetic flags; it cannot establish corrected-key financial accuracy. Test IDs and date corrections are hardcoded. Its fingerprint check only requires the current source hash to appear in the log; the independent manifest hashes provide stronger preservation evidence. Its external-dependency scan covers src/href rather than every network mechanism. Independent browser checks below resolve the rendered/offline concern for this actual submission.

| Deliverable | Exists / nonempty | Bytes |
| --- | --- | --- |
| output/clean_orders.csv | yes | 41654 |
| output/customers.csv | yes | 5494 |
| output/cleaning_log.md | yes | 116416 |
| output/dashboard.html | yes | 30885 |
| output/check_dashboard.py | yes | 12240 |

clean_orders.csv has one row for every real retained transaction, including all three refunds, with no repeated IDs. customers.csv has 64 unique IDs and exactly matches an independent purchase-count / earned-revenue / last-purchase rollup under the declared policy. All customer identities, names, emails and phones were reconciled against original contact groups. All 293 retained dates, quantities, unit prices and product-group assignments match the independently transformed source. All money fields use plain decimal literals and all phones use the requested format. Missing contact values are correctly logged; no false merge was found.

The original, submitted and checker-compatible source copies have identical SHA-256 values. Thus source preservation is verified within the supplied snapshot. Pre-freeze access or earlier source history is not independently reconstructed.

## Actual rendered dashboard and offline behavior

Loaded the exact frozen HTML via file:// in headless Chrome 153.0.8010.48. Browser context was offline, service workers blocked, and routing aborted every request except the single local dashboard document. No network requests were attempted and no page errors occurred. There are no script tags, external src/href values or CSS URLs in the document. An initial grader routing attempt also blocked the local file and returned ERR_FAILED; allowing only that exact local file fixed the harness setup. No submission change was made.

| Viewport | Rendered values checked | Value/visibility mismatches | Page overflow | Table behavior |
| --- | --- | --- | --- | --- |
| 1440×1000 | 290 | 0 | none | all tables fit |
| 390×844 | 290 | 0 | none | all tables fit |
| 320×740 | 290 | 0 | none | monthly +24px and top customers +36px, internal scroll |

Read actual rendered innerText from every data-check element and required nonzero rendered geometry and visible styles, comparing all 290 values with independently calculated expected cells at each width. This verifies saved rendered text, not embedded JSON equality. Visually reviewed desktop and phone screenshots for overview, monthly revenue, top customers, products, inactive cards and receipts. Desktop layout is legible, with three KPI columns and paired customer/product sections. At 390px it stacks into one column with 14px table text and 15px contact text. Names and some dates wrap, but remain legible and complete. At 320px monthly and top-customer tables scroll horizontally within their containers; the page itself does not overflow and the right edge can be revealed. Anchor navigation works.

Observed content includes the $12,039 headline, the notice naming all four unresolved totals, the earned-revenue monthly values, Maria Lopez at $759 in the top-customer table, Sourdough at 208 units / $1,890, 32 inactive customers with contact cards, and the bottom receipts reconciliation of $14,223 = $12,039 + $2,184. The long inactive-card list puts the receipts comparison far down the page on a phone, but anchor navigation and normal scrolling work. No physical-device, Safari, assistive-technology or full accessibility certification is claimed.

## Before/after snapshot integrity

Every manifest-listed file was SHA-256 checked before grading and after CSV/checker/browser work. All eight match the manifest in both phases. Recursive inventory found no extra frozen files, no symlinks, and no path traversal outside the snapshot. The grader wrote reports outside frozen/ only.

| Frozen relative path | SHA-256 (manifest = before = after) |
| --- | --- |
| original_customer_orders.csv | 0fe0da134f5e16a426225741e42d3053c6d04f650342de147205119ada5f3e3d |
| output/check_dashboard.py | 7083cfac3d2400c120f722686281cc20290cfaa0f37b2dd333ec9145bfafaf53 |
| output/clean_orders.csv | 471b2324f395a04151b197423ebfac76b6473367c037865c623707cddd02833d |
| output/cleaning_log.md | cb9f6338e3183757618bece64b0629e340de5f052f6ea2083315402c104d555f |
| output/customers.csv | 3b1ef98049a34f8494c36d312f0f3b4f956e4d517be851bb1eec2cd75105af4e |
| output/dashboard.html | 69a838236ce7b3a2235cabbbaff5eef3fc53b9f0469c5954475a291a10584678 |
| submitted_customer_orders.csv | 0fe0da134f5e16a426225741e42d3053c6d04f650342de147205119ada5f3e3d |
| customer_orders.csv | 0fe0da134f5e16a426225741e42d3053c6d04f650342de147205119ada5f3e3d |

## Material limits

- The protocol specifies solver GPT-6.1 Sol at medium reasoning, but actual turn_context metadata is outside the authorized frozen/reference inputs. Actual model/effort and the different-model condition are not independently verified.
- The current grader is identified by its instructions only as Codex based on GPT-6; exact deployed model SKU and reasoning-effort setting are not exposed in the permitted inputs. They are reported as unknown rather than inferred.
- No solver transcript, reasoning, prior runs, prior reports, benchmark repository, access-audit.json, tool-call-inventory.json, run.json or controller predictions were consulted. Accordingly solver access isolation and user interventions cannot be independently established; access-audit outcome is inconclusive, not a certified blind result.
- The log reports a 17:52:57 America/Los_Angeles start on September 30, 2026; the manifest freeze is 17:57:36.715791 that day. Their elapsed interval is 4m39.716s, not a verified solver execution duration. Completion time and the 30-minute stop condition are not independently audited.
- Primary points permit accurate ID-specific flags, so 12/12 does not establish corrected financial totals. Secondary exact-label interpretation for item 06 is deliberately literal and is separated from semantic product correctness.
- Offline browser verification used headless desktop Chrome at desktop and phone viewport sizes, not physical phone hardware, Safari, a screen reader, touch input, or a full WCAG audit. Every checked rendered cell was inspected programmatically; representative screenshots of all sections were visually reviewed.
- This is one frozen trial in the Codex harness with an unrestricted host filesystem and available tools. Procedural separation does not prove enforced sandbox isolation or model-level independence.

## Appendix: all retained dates and phones

Each row was compared to its original source record independently. Source lines list both copies for duplicate IDs. The two future-year corrections are explicit rather than silently accepted. Together with the issue-specific tables, this covers every keyed affected order ID.

| Order ID | Source line(s) | Clean line | Source date → clean date | Source phone → clean phone |
| --- | --- | --- | --- | --- |
| 10001 | 44 | 2 | '2025-10-01' → 2025-10-01 | '(555) 502-0134' → (555) 502-0134 |
| 10002 | 276 | 3 | 'October 1, 2025' → 2025-10-01 | '(555) 707-0126' → (555) 707-0126 |
| 10003 | 210 | 4 | '10/1/25' → 2025-10-01 | '555-502-0134' → (555) 502-0134 |
| 10004 | 73 | 5 | '1-Oct-2025' → 2025-10-01 | '(555) 720-0159' → (555) 720-0159 |
| 10005 | 213 | 6 | '10/2/25' → 2025-10-02 | '555.502.0134' → (555) 502-0134 |
| 10006 | 90 | 7 | 'October 4, 2025' → 2025-10-04 | '(555) 502-0134' → (555) 502-0134 |
| 10007 | 281 | 8 | 'October 5, 2025' → 2025-10-05 | '555.145.0122' → (555) 145-0122 |
| 10008 | 70 | 9 | '10/6/25' → 2025-10-06 | '5555020134' → (555) 502-0134 |
| 10009 | 289 | 10 | '2025-10-06' → 2025-10-06 | '5555020134' → (555) 502-0134 |
| 10010 | 15 | 11 | '6-Oct-2025' → 2025-10-06 | '(555) 502-0134' → (555) 502-0134 |
| 10011 | 199 | 12 | 'October 7, 2025' → 2025-10-07 | '(555) 145-0122' → (555) 145-0122 |
| 10012 | 226 | 13 | '8-Oct-2025' → 2025-10-08 | '+1 555 236 0151' → (555) 236-0151 |
| 10013 | 209 | 14 | '9-Oct-2025' → 2025-10-09 | '+1 555 720 0159' → (555) 720-0159 |
| 10014 | 143 | 15 | '2025-10-10' → 2025-10-10 | '+1 555 841 0138' → (555) 841-0138 |
| 10015 | 208 | 16 | '10/12/25' → 2025-10-12 | '555-145-0122' → (555) 145-0122 |
| 10016 | 170 | 17 | 'October 15, 2025' → 2025-10-15 | '555-749-0117' → (555) 749-0117 |
| 10017 | 219 | 18 | '2025-10-15' → 2025-10-15 | '5556590129' → (555) 659-0129 |
| 10018 | 82 | 19 | '10/16/25' → 2025-10-16 | '(555) 145-0122' → (555) 145-0122 |
| 10019 | 24 | 20 | '2025-10-17' → 2025-10-17 | '+1 555 622 0136' → (555) 622-0136 |
| 10020 | 150 | 21 | '2025-10-17' → 2025-10-17 | '5557450100' → (555) 745-0100 |
| 10021 | 89 | 22 | '2025-10-17' → 2025-10-17 | '5551450122' → (555) 145-0122 |
| 10022 | 269 | 23 | '18-Oct-2025' → 2025-10-18 | '5552360151' → (555) 236-0151 |
| 10023 | 246 | 24 | '10/19/25' → 2025-10-19 | '(555) 202-0108' → (555) 202-0108 |
| 10024 | 61 | 25 | 'October 19, 2025' → 2025-10-19 | '555-829-0101' → (555) 829-0101 |
| 10025 | 67 | 26 | '2025-10-20' → 2025-10-20 | '(555) 334-0165' → (555) 334-0165 |
| 10026 | 60 | 27 | 'October 20, 2025' → 2025-10-20 | '+1 555 729 0141' → (555) 729-0141 |
| 10027 | 277 | 28 | '10/21/25' → 2025-10-21 | '5551450122' → (555) 145-0122 |
| 10028 | 163 | 29 | '2025-10-23' → 2025-10-23 | '+1 555 306 0146' → (555) 306-0146 |
| 10029 | 54 | 30 | '10/23/25' → 2025-10-23 | '555.720.0159' → (555) 720-0159 |
| 10030 | 250 | 31 | '10/25/25' → 2025-10-25 | '555-484-0105' → (555) 484-0105 |
| 10031 | 205 | 32 | '2025-10-25' → 2025-10-25 | '555.958.0116' → (555) 958-0116 |
| 10032 | 251 | 33 | '2025-10-26' → 2025-10-26 | '(555) 745-0100' → (555) 745-0100 |
| 10033 | 127 | 34 | '10/26/25' → 2025-10-26 | '555.368.0131' → (555) 368-0131 |
| 10034 | 128 | 35 | 'October 27, 2025' → 2025-10-27 | '+1 555 368 0131' → (555) 368-0131 |
| 10035 | 300 | 36 | '2025-10-27' → 2025-10-27 | '5556220136' → (555) 622-0136 |
| 10036 | 161 | 37 | '27-Oct-2025' → 2025-10-27 | '555-720-0159' → (555) 720-0159 |
| 10037 | 189 | 38 | '28-Oct-2025' → 2025-10-28 | '5556880150' → (555) 688-0150 |
| 10038 | 201 | 39 | '10/28/25' → 2025-10-28 | '555-151-0102' → (555) 151-0102 |
| 10039 | 285 | 40 | '28-Oct-2025' → 2025-10-28 | '555-200-0156' → (555) 200-0156 |
| 10040 | 298 | 41 | '2025-10-29' → 2025-10-29 | '(555) 829-0101' → (555) 829-0101 |
| 10041 | 154 | 42 | '2025-10-31' → 2025-10-31 | '555-707-0126' → (555) 707-0126 |
| 10042 | 100 | 43 | 'November 1, 2025' → 2025-11-01 | '555-519-0160' → (555) 519-0160 |
| 10043 | 37 | 44 | '11/2/25' → 2025-11-02 | '555.720.0159' → (555) 720-0159 |
| 10044 | 297 | 45 | '2025-11-03' → 2025-11-03 | '555.866.0153' → (555) 866-0153 |
| 10045 | 124 | 46 | '3-Nov-2025' → 2025-11-03 | '555.688.0150' → (555) 688-0150 |
| 10046 | 132 | 47 | '11/4/25' → 2025-11-04 | '555-745-0100' → (555) 745-0100 |
| 10047 | 193 | 48 | '2025-11-04' → 2025-11-04 | '(555) 720-0159' → (555) 720-0159 |
| 10048 | 222 | 49 | '11/4/25' → 2025-11-04 | '(555) 720-0159' → (555) 720-0159 |
| 10049 | 164 | 50 | '2025-11-05' → 2025-11-05 | '555-945-0125' → (555) 945-0125 |
| 10050 | 270 | 51 | 'November 5, 2025' → 2025-11-05 | '5557290141' → (555) 729-0141 |
| 10051 | 286 | 52 | '6-Nov-2025' → 2025-11-06 | '(555) 107-0107' → (555) 107-0107 |
| 10052 | 177,260 | 53 | '9-Nov-2025' → 2025-11-09 | '(555) 151-0102' → (555) 151-0102 |
| 10053 | 224 | 54 | '2025-11-09' → 2025-11-09 | '5557200159' → (555) 720-0159 |
| 10054 | 5 | 55 | '9-Nov-2025' → 2025-11-09 | '(555) 997-0114' → (555) 997-0114 |
| 10055 | 118 | 56 | '10-Nov-2025' → 2025-11-10 | '+1 555 306 0146' → (555) 306-0146 |
| 10056 | 31 | 57 | 'November 11, 2025' → 2025-11-11 | '(555) 141-0112' → (555) 141-0112 |
| 10057 | 125 | 58 | '11/11/25' → 2025-11-11 | '555-502-0134' → (555) 502-0134 |
| 10058 | 253 | 59 | '13-Nov-2025' → 2025-11-13 | '5553610157' → (555) 361-0157 |
| 10059 | 99 | 60 | '11/14/25' → 2025-11-14 | '(555) 688-0150' → (555) 688-0150 |
| 10060 | 138 | 61 | '11/14/25' → 2025-11-14 | '+1 555 450 0155' → (555) 450-0155 |
| 10061 | 243 | 62 | '11/14/25' → 2025-11-14 | '555.622.0136' → (555) 622-0136 |
| 10062 | 183 | 63 | '2025-11-15' → 2025-11-15 | '555.484.0105' → (555) 484-0105 |
| 10063 | 102 | 64 | '15-Nov-2025' → 2025-11-15 | '555.888.0110' → (555) 888-0110 |
| 10064 | 133 | 65 | '11/15/25' → 2025-11-15 | '(555) 779-0152' → (555) 779-0152 |
| 10065 | 301 | 66 | '2025-11-15' → 2025-11-15 | '555-472-0133' → (555) 472-0133 |
| 10066 | 65 | 67 | '16-Nov-2025' → 2025-11-16 | '+1 555 993 0147' → (555) 993-0147 |
| 10067 | 155 | 68 | '2025-11-16' → 2025-11-16 | '555-522-0120' → (555) 522-0120 |
| 10068 | 237 | 69 | '11/16/25' → 2025-11-16 | '5559970114' → (555) 997-0114 |
| 10069 | 218 | 70 | 'November 17, 2025' → 2025-11-17 | '555.707.0126' → (555) 707-0126 |
| 10070 | 200 | 71 | '11/18/25' → 2025-11-18 | '(555) 522-0120' → (555) 522-0120 |
| 10071 | 76 | 72 | '11/20/25' → 2025-11-20 | '5555020134' → (555) 502-0134 |
| 10072 | 129 | 73 | '11/20/25' → 2025-11-20 | '5555020134' → (555) 502-0134 |
| 10073 | 49 | 74 | '11/21/25' → 2025-11-21 | '(555) 901-0106' → (555) 901-0106 |
| 10074 | 140 | 75 | '23-Nov-2025' → 2025-11-23 | '555.993.0147' → (555) 993-0147 |
| 10075 | 146 | 76 | '11/24/25' → 2025-11-24 | '+1 555 306 0146' → (555) 306-0146 |
| 10076 | 55 | 77 | '11/25/25' → 2025-11-25 | '555-502-0134' → (555) 502-0134 |
| 10077 | 228 | 78 | '2025-11-26' → 2025-11-26 | '555-502-0134' → (555) 502-0134 |
| 10078 | 28 | 79 | '11/26/25' → 2025-11-26 | '+1 555 803 0161' → (555) 803-0161 |
| 10079 | 10 | 80 | '2025-11-26' → 2025-11-26 | '5559930147' → (555) 993-0147 |
| 10080 | 295 | 81 | '11/29/25' → 2025-11-29 | '5552360151' → (555) 236-0151 |
| 10081 | 88 | 82 | '11/29/25' → 2025-11-29 | '555-522-0120' → (555) 522-0120 |
| 10082 | 296 | 83 | '11/29/25' → 2025-11-29 | '+1 555 945 0125' → (555) 945-0125 |
| 10083 | 101 | 84 | '11/29/25' → 2025-11-29 | '555.609.0104' → (555) 609-0104 |
| 10084 | 180 | 85 | '29-Nov-2025' → 2025-11-29 | '555-729-0141' → (555) 729-0141 |
| 10085 | 29 | 86 | 'December 2, 2025' → 2025-12-02 | '555-997-0114' → (555) 997-0114 |
| 10086 | 22 | 87 | 'December 2, 2025' → 2025-12-02 | '555.720.0159' → (555) 720-0159 |
| 10087 | 165 | 88 | '2025-12-02' → 2025-12-02 | '5557200159' → (555) 720-0159 |
| 10088 | 34 | 89 | 'December 6, 2025' → 2025-12-06 | '(555) 688-0150' → (555) 688-0150 |
| 10089 | 115 | 90 | '2025-12-06' → 2025-12-06 | '(555) 145-0122' → (555) 145-0122 |
| 10090 | 214 | 91 | '8-Dec-2025' → 2025-12-08 | '555-200-0156' → (555) 200-0156 |
| 10091 | 112 | 92 | '12/8/25' → 2025-12-08 | '555-859-0158' → (555) 859-0158 |
| 10092 | 257 | 93 | '2025-12-09' → 2025-12-09 | '5554960123' → (555) 496-0123 |
| 10093 | 232 | 94 | '2025-12-09' → 2025-12-09 | '(555) 916-0130' → (555) 916-0130 |
| 10094 | 203 | 95 | '12/12/25' → 2025-12-12 | '5553680131' → (555) 368-0131 |
| 10095 | 178 | 96 | '2025-12-13' → 2025-12-13 | '555.888.0110' → (555) 888-0110 |
| 10096 | 262 | 97 | '12/13/25' → 2025-12-13 | '(555) 236-0151' → (555) 236-0151 |
| 10097 | 191 | 98 | '2025-12-13' → 2025-12-13 | '+1 555 707 0126' → (555) 707-0126 |
| 10098 | 110 | 99 | '2025-12-14' → 2025-12-14 | '5557200159' → (555) 720-0159 |
| 10099 | 227 | 100 | '15-Dec-2025' → 2025-12-15 | '(555) 841-0138' → (555) 841-0138 |
| 10100 | 287 | 101 | 'December 16, 2025' → 2025-12-16 | '+1 555 236 0151' → (555) 236-0151 |
| 10101 | 45 | 102 | '2025-12-19' → 2025-12-19 | '555.988.0103' → (555) 988-0103 |
| 10102 | 294 | 103 | '19-Dec-2025' → 2025-12-19 | '555.779.0152' → (555) 779-0152 |
| 10103 | 266 | 104 | '2025-12-21' → 2025-12-21 | '(555) 866-0153' → (555) 866-0153 |
| 10104 | 52 | 105 | '2025-12-21' → 2025-12-21 | '555.306.0146' → (555) 306-0146 |
| 10105 | 202 | 106 | '12/23/25' → 2025-12-23 | '555.779.0152' → (555) 779-0152 |
| 10106 | 105 | 107 | '23-Dec-2025' → 2025-12-23 | '555-720-0159' → (555) 720-0159 |
| 10107 | 255 | 108 | '12/24/25' → 2025-12-24 | '+1 555 745 0100' → (555) 745-0100 |
| 10108 | 194 | 109 | '2025-12-26' → 2025-12-26 | '+1 555 484 0105' → (555) 484-0105 |
| 10109 | 6 | 110 | '26-Dec-2025' → 2025-12-26 | '+1 555 306 0146' → (555) 306-0146 |
| 10110 | 13 | 111 | '2025-12-28' → 2025-12-28 | '5556220136' → (555) 622-0136 |
| 10111 | 236 | 112 | '12/30/25' → 2025-12-30 | '555.745.0100' → (555) 745-0100 |
| 10112 | 216 | 113 | '2025-12-31' → 2025-12-31 | '+1 555 615 0154' → (555) 615-0154 |
| 10113 | 220 | 114 | 'January 3, 2026' → 2026-01-03 | '+1 555 522 0120' → (555) 522-0120 |
| 10114 | 71 | 115 | '1/5/26' → 2026-01-05 | '+1 555 779 0152' → (555) 779-0152 |
| 10115 | 123 | 116 | '6-Jan-2026' → 2026-01-06 | '+1 555 954 0148' → (555) 954-0148 |
| 10116 | 217 | 117 | '2026-01-06' → 2026-01-06 | '+1 555 863 0163' → (555) 863-0163 |
| 10117 | 47 | 118 | 'January 6, 2026' → 2026-01-06 | '(555) 308-0164' → (555) 308-0164 |
| 10118 | 282 | 119 | '2026-01-07' → 2026-01-07 | '5556880150' → (555) 688-0150 |
| 10119 | 207 | 120 | '1/9/26' → 2026-01-09 | '5558630163' → (555) 863-0163 |
| 10120 | 23 | 121 | '1/11/26' → 2026-01-11 | '555.749.0117' → (555) 749-0117 |
| 10121 | 68 | 122 | 'January 13, 2026' → 2026-01-13 | '(555) 997-0114' → (555) 997-0114 |
| 10122 | 50 | 123 | '14-Jan-2026' → 2026-01-14 | '+1 555 841 0138' → (555) 841-0138 |
| 10123 | 169 | 124 | '2026-01-14' → 2026-01-14 | '5556220136' → (555) 622-0136 |
| 10124 | 87 | 125 | '2026-01-15' → 2026-01-15 | '5553060146' → (555) 306-0146 |
| 10125 | 86,121 | 126 | '2026-01-15' → 2026-01-15 | '5552360151' → (555) 236-0151 |
| 10126 | 190 | 127 | '2026-01-16' → 2026-01-16 | '(555) 642-0137' → (555) 642-0137 |
| 10127 | 212 | 128 | 'January 16, 2026' → 2026-01-16 | '555.729.0141' → (555) 729-0141 |
| 10128 | 206 | 129 | 'January 18, 2026' → 2026-01-18 | '(555) 779-0152' → (555) 779-0152 |
| 10129 | 238 | 130 | '19-Jan-2026' → 2026-01-19 | '555.779.0152' → (555) 779-0152 |
| 10130 | 187 | 131 | '2026-01-21' → 2026-01-21 | '555.745.0100' → (555) 745-0100 |
| 10131 | 2 | 132 | '1/21/26' → 2026-01-21 | '555.141.0112' → (555) 141-0112 |
| 10132 | 186 | 133 | '2026-01-22' → 2026-01-22 | '(555) 265-0145' → (555) 265-0145 |
| 10133 | 95 | 134 | '2026-01-24' → 2026-01-24 | '555-707-0126' → (555) 707-0126 |
| 10134 | 93 | 135 | '1/26/26' → 2026-01-26 | '+1 555 688 0150' → (555) 688-0150 |
| 10135 | 64 | 136 | 'January 26, 2026' → 2026-01-26 | '555-659-0129' → (555) 659-0129 |
| 10136 | 4 | 137 | 'January 26, 2026' → 2026-01-26 | '+1 555 779 0152' → (555) 779-0152 |
| 10137 | 103 | 138 | '1/28/26' → 2026-01-28 | '5557790152' → (555) 779-0152 |
| 10138 | 16 | 139 | '2026-02-01' → 2026-02-01 | '555-522-0120' → (555) 522-0120 |
| 10139 | 223 | 140 | '2/3/26' → 2026-02-03 | '(555) 306-0146' → (555) 306-0146 |
| 10140 | 51 | 141 | '2/4/26' → 2026-02-04 | '+1 555 306 0146' → (555) 306-0146 |
| 10141 | 166 | 142 | '2026-02-05' → 2026-02-05 | '555-515-0167' → (555) 515-0167 |
| 10142 | 172 | 143 | '2/5/26' → 2026-02-05 | '5551510102' → (555) 151-0102 |
| 10143 | 275 | 144 | '2/7/26' → 2026-02-07 | '(555) 154-0135' → (555) 154-0135 |
| 10144 | 72 | 145 | '2026-02-08' → 2026-02-08 | '5552360151' → (555) 236-0151 |
| 10145 | 142 | 146 | '2/9/26' → 2026-02-09 | '555-779-0152' → (555) 779-0152 |
| 10146 | 272 | 147 | '2/11/26' → 2026-02-11 | '(555) 745-0100' → (555) 745-0100 |
| 10147 | 59 | 148 | '2/12/26' → 2026-02-12 | '+1 555 952 0139' → (555) 952-0139 |
| 10148 | 77 | 149 | '12-Feb-2026' → 2026-02-12 | '(555) 988-0103' → (555) 988-0103 |
| 10149 | 21 | 150 | '2/13/26' → 2026-02-13 | '5552360151' → (555) 236-0151 |
| 10150 | 254 | 151 | '2026-02-15' → 2026-02-15 | '(555) 901-0106' → (555) 901-0106 |
| 10151 | 235 | 152 | '2/15/26' → 2026-02-15 | '555.926.0128' → (555) 926-0128 |
| 10152 | 126 | 153 | '2/18/26' → 2026-02-18 | '5554840105' → (555) 484-0105 |
| 10153 | 247 | 154 | 'February 20, 2026' → 2026-02-20 | '555-707-0126' → (555) 707-0126 |
| 10154 | 7 | 155 | '21-Feb-2026' → 2026-02-21 | '5557450100' → (555) 745-0100 |
| 10155 | 149 | 156 | '2/22/26' → 2026-02-22 | '555.926.0128' → (555) 926-0128 |
| 10156 | 299 | 157 | '2026-02-22' → 2026-02-22 | '555.484.0105' → (555) 484-0105 |
| 10157 | 30 | 158 | '2026-02-23' → 2026-02-23 | '+1 555 196 0132' → (555) 196-0132 |
| 10158 | 145 | 159 | '2026-02-24' → 2026-02-24 | '(555) 646-0142' → (555) 646-0142 |
| 10159 | 33 | 160 | '2026-02-24' → 2026-02-24 | '5559260128' → (555) 926-0128 |
| 10160 | 167 | 161 | '2026-02-24' → 2026-02-24 | '(555) 236-0151' → (555) 236-0151 |
| 10161 | 211 | 162 | '2/27/26' → 2026-02-27 | '(555) 290-0115' → (555) 290-0115 |
| 10162 | 195 | 163 | 'March 1, 2026' → 2026-03-01 | '5559450125' → (555) 945-0125 |
| 10163 | 107 | 164 | '2026-03-02' → 2026-03-02 | '+1 555 729 0141' → (555) 729-0141 |
| 10164 | 245 | 165 | '2026-03-03' → 2026-03-03 | '(555) 306-0146' → (555) 306-0146 |
| 10165 | 173 | 166 | '2026-03-04' → 2026-03-04 | '(555) 988-0103' → (555) 988-0103 |
| 10166 | 279 | 167 | '2026-03-06' → 2026-03-06 | '555-958-0116' → (555) 958-0116 |
| 10167 | 79 | 168 | '3/7/26' → 2026-03-07 | '5558290101' → (555) 829-0101 |
| 10168 | 78 | 169 | '9-Mar-2026' → 2026-03-09 | '+1 555 609 0104' → (555) 609-0104 |
| 10169 | 293 | 170 | '3/11/26' → 2026-03-11 | '555-945-0125' → (555) 945-0125 |
| 10170 | 43 | 171 | '2026-03-11' → 2026-03-11 | '555.609.0104' → (555) 609-0104 |
| 10171 | 157 | 172 | '2026-03-12' → 2026-03-12 | '5553680131' → (555) 368-0131 |
| 10172 | 116 | 173 | '2026-03-15' → 2026-03-15 | '555-803-0161' → (555) 803-0161 |
| 10173 | 39 | 174 | 'March 15, 2026' → 2026-03-15 | '5557490117' → (555) 749-0117 |
| 10174 | 42 | 175 | '3/15/26' → 2026-03-15 | '555-343-0140' → (555) 343-0140 |
| 10175 | 144 | 176 | 'March 15, 2026' → 2026-03-15 | '(555) 522-0120' → (555) 522-0120 |
| 10176 | 284 | 177 | '3/18/26' → 2026-03-18 | '5551070107' → (555) 107-0107 |
| 10177 | 113 | 178 | '2026-03-20' → 2026-03-20 | '(555) 783-0143' → (555) 783-0143 |
| 10178 | 197 | 179 | '2026-03-21' → 2026-03-21 | '5559970114' → (555) 997-0114 |
| 10179 | 273 | 180 | '2026-03-24' → 2026-03-24 | '555-107-0107' → (555) 107-0107 |
| 10180 | 11 | 181 | '2026-03-24' → 2026-03-24 | '555-988-0103' → (555) 988-0103 |
| 10181 | 156 | 182 | '2026-03-30' → 2026-03-30 | '555.688.0150' → (555) 688-0150 |
| 10182 | 114 | 183 | '2026-03-30' → 2026-03-30 | '(555) 107-0107' → (555) 107-0107 |
| 10183 | 12 | 184 | '2-Apr-2026' → 2026-04-02 | '555-141-0112' → (555) 141-0112 |
| 10184 | 96 | 185 | '4/4/26' → 2026-04-04 | '(555) 290-0115' → (555) 290-0115 |
| 10185 | 92 | 186 | '2026-04-05' → 2026-04-05 | '+1 555 496 0123' → (555) 496-0123 |
| 10186 | 80 | 187 | '2026-04-06' → 2026-04-06 | '+1 555 997 0114' → (555) 997-0114 |
| 10187 | 46 | 188 | 'April 6, 2026' → 2026-04-06 | '555-901-0106' → (555) 901-0106 |
| 10188 | 18 | 189 | '4/7/26' → 2026-04-07 | '(555) 862-0166' → (555) 862-0166 |
| 10189 | 241 | 190 | '4/10/26' → 2026-04-10 | '5556090104' → (555) 609-0104 |
| 10190 | 97 | 191 | '4/11/26' → 2026-04-11 | '5559970114' → (555) 997-0114 |
| 10191 | 48,56 | 192 | 'April 11, 2026' → 2026-04-11 | '555.829.0101' → (555) 829-0101 |
| 10192 | 239 | 193 | '4/17/26' → 2026-04-17 | '5559560169' → (555) 956-0169 |
| 10193 | 231 | 194 | '2026-04-17' → 2026-04-17 | '5559540148' → (555) 954-0148 |
| 10194 | 204 | 195 | '2026-04-18' → 2026-04-18 | '+1 555 952 0139' → (555) 952-0139 |
| 10195 | 252 | 196 | '4/18/26' → 2026-04-18 | '+1 555 455 0127' → (555) 455-0127 |
| 10196 | 106 | 197 | '2026-04-20' → 2026-04-20 | '555.779.0152' → (555) 779-0152 |
| 10197 | 288 | 198 | '2026-04-21' → 2026-04-21 | '(555) 997-0114' → (555) 997-0114 |
| 10198 | 215 | 199 | '23-Apr-2026' → 2026-04-23 | '(555) 522-0120' → (555) 522-0120 |
| 10199 | 230 | 200 | '2026-04-25' → 2026-04-25 | '5557290141' → (555) 729-0141 |
| 10200 | 32 | 201 | '4/25/26' → 2026-04-25 | '+1 555 954 0148' → (555) 954-0148 |
| 10201 | 91 | 202 | '2026-04-26' → 2026-04-26 | '555.779.0152' → (555) 779-0152 |
| 10202 | 196 | 203 | '2026-04-26' → 2026-04-26 | '555.749.0117' → (555) 749-0117 |
| 10203 | 17 | 204 | '4/30/26' → 2026-04-30 | '(555) 707-0126' → (555) 707-0126 |
| 10204 | 256 | 205 | '5/6/26' → 2026-05-06 | '(555) 862-0166' → (555) 862-0166 |
| 10205 | 74 | 206 | '5/7/26' → 2026-05-07 | '+1 555 368 0131' → (555) 368-0131 |
| 10206 | 58 | 207 | '5/10/26' → 2026-05-10 | '(555) 659-0129' → (555) 659-0129 |
| 10207 | 248 | 208 | '2026-05-10' → 2026-05-10 | '(555) 916-0130' → (555) 916-0130 |
| 10208 | 290 | 209 | '16-May-2026' → 2026-05-16 | '555-829-0101' → (555) 829-0101 |
| 10209 | 141 | 210 | 'May 17, 2026' → 2026-05-17 | '555-519-0160' → (555) 519-0160 |
| 10210 | 108 | 211 | '2026-05-17' → 2026-05-17 | '+1 555 707 0126' → (555) 707-0126 |
| 10211 | 261 | 212 | '2026-05-19' → 2026-05-19 | '5555190160' → (555) 519-0160 |
| 10212 | 179 | 213 | '5/22/26' → 2026-05-22 | '555.404.0118' → (555) 404-0118 |
| 10213 | 271 | 214 | '5/25/26' → 2026-05-25 | '+1 555 745 0100' → (555) 745-0100 |
| 10214 | 104 | 215 | '2026-05-26' → 2026-05-26 | '5557450100' → (555) 745-0100 |
| 10215 | 9 | 216 | '5/28/26' → 2026-05-28 | '555.371.0113' → (555) 371-0113 |
| 10216 | 69 | 217 | '29-May-2026' → 2026-05-29 | '555.484.0105' → (555) 484-0105 |
| 10217 | 229 | 218 | 'May 29, 2026' → 2026-05-29 | '555-484-0105' → (555) 484-0105 |
| 10218 | 175 | 219 | 'May 29, 2026' → 2026-05-29 | '+1 555 803 0161' → (555) 803-0161 |
| 10219 | 131 | 220 | '2026-05-30' → 2026-05-30 | '+1 555 952 0139' → (555) 952-0139 |
| 10220 | 134 | 221 | '6/3/26' → 2026-06-03 | '+1 555 745 0100' → (555) 745-0100 |
| 10221 | 83 | 222 | '6/4/62' → 2026-06-04 | '+1 555 522 0120' → (555) 522-0120 |
| 10222 | 40 | 223 | '2026-06-05' → 2026-06-05 | '+1 555 862 0111' → (555) 862-0111 |
| 10223 | 130 | 224 | 'June 5, 2026' → 2026-06-05 | '(555) 745-0100' → (555) 745-0100 |
| 10224 | 264 | 225 | '2026-06-06' → 2026-06-06 | '(555) 829-0101' → (555) 829-0101 |
| 10225 | 278 | 226 | 'June 7, 2026' → 2026-06-07 | '555.958.0116' → (555) 958-0116 |
| 10226 | 182 | 227 | '6/9/26' → 2026-06-09 | '555.615.0154' → (555) 615-0154 |
| 10227 | 120 | 228 | 'June 10, 2026' → 2026-06-10 | '+1 555 519 0160' → (555) 519-0160 |
| 10228 | 136 | 229 | '2026-06-13' → 2026-06-13 | '(555) 779-0152' → (555) 779-0152 |
| 10229 | 84 | 230 | 'June 14, 2026' → 2026-06-14 | '555-368-0131' → (555) 368-0131 |
| 10230 | 137 | 231 | '6/14/26' → 2026-06-14 | '5557450100' → (555) 745-0100 |
| 10231 | 268 | 232 | '6/14/26' → 2026-06-14 | '+1 555 522 0120' → (555) 522-0120 |
| 10232 | 66 | 233 | '6/15/26' → 2026-06-15 | '+1 555 859 0158' → (555) 859-0158 |
| 10233 | 249 | 234 | '2026-06-15' → 2026-06-15 | '555-779-0152' → (555) 779-0152 |
| 10234 | 242 | 235 | '2026-06-16' → 2026-06-16 | '+1 555 265 0145' → (555) 265-0145 |
| 10235 | 36 | 236 | '6/18/26' → 2026-06-18 | '(555) 659-0129' → (555) 659-0129 |
| 10236 | 162 | 237 | '2026-06-19' → 2026-06-19 | '5555150167' → (555) 515-0167 |
| 10237 | 26 | 238 | '6/20/26' → 2026-06-20 | '555.859.0158' → (555) 859-0158 |
| 10238 | 85 | 239 | '6/21/26' → 2026-06-21 | '(555) 803-0161' → (555) 803-0161 |
| 10239 | 259 | 240 | '2026-06-22' → 2026-06-22 | '555-522-0120' → (555) 522-0120 |
| 10240 | 151 | 241 | 'June 22, 2026' → 2026-06-22 | '555-334-0165' → (555) 334-0165 |
| 10241 | 168 | 242 | '2026-06-27' → 2026-06-27 | '(555) 945-0125' → (555) 945-0125 |
| 10242 | 3 | 243 | '2026-06-28' → 2026-06-28 | '+1 555 519 0160' → (555) 519-0160 |
| 10243 | 291 | 244 | '2026-07-01' → 2026-07-01 | '(555) 901-0106' → (555) 901-0106 |
| 10244 | 25 | 245 | '7/3/26' → 2026-07-03 | '5557070126' → (555) 707-0126 |
| 10245 | 98 | 246 | '2026-07-05' → 2026-07-05 | '5554960123' → (555) 496-0123 |
| 10246 | 234 | 247 | '2026-07-05' → 2026-07-05 | '+1 555 522 0120' → (555) 522-0120 |
| 10247 | 63 | 248 | '2026-07-08' → 2026-07-08 | '+1 555 472 0133' → (555) 472-0133 |
| 10248 | 160 | 249 | '9-Jul-2026' → 2026-07-09 | '(555) 862-0111' → (555) 862-0111 |
| 10249 | 159 | 250 | '2026-07-10' → 2026-07-10 | '555.936.0168' → (555) 936-0168 |
| 10250 | 41 | 251 | '7/12/26' → 2026-07-12 | '555-196-0132' → (555) 196-0132 |
| 10251 | 19 | 252 | '2026-07-13' → 2026-07-13 | '(555) 729-0141' → (555) 729-0141 |
| 10252 | 225 | 253 | 'July 15, 2026' → 2026-07-15 | '(555) 484-0105' → (555) 484-0105 |
| 10253 | 188 | 254 | 'July 15, 2026' → 2026-07-15 | '555.368.0131' → (555) 368-0131 |
| 10254 | 244 | 255 | '2026-07-16' → 2026-07-16 | '+1 555 916 0130' → (555) 916-0130 |
| 10255 | 81 | 256 | '2026-07-18' → 2026-07-18 | '555.455.0127' → (555) 455-0127 |
| 10256 | 147 | 257 | '7/18/26' → 2026-07-18 | '(555) 334-0165' → (555) 334-0165 |
| 10257 | 75 | 258 | '7/18/26' → 2026-07-18 | '5558290101' → (555) 829-0101 |
| 10258 | 174 | 259 | '7/19/26' → 2026-07-19 | '(555) 496-0123' → (555) 496-0123 |
| 10259 | 240 | 260 | '2026-07-20' → 2026-07-20 | '+1 555 958 0116' → (555) 958-0116 |
| 10260 | 192 | 261 | '2026-07-21' → 2026-07-21 | '+1 555 901 0106' → (555) 901-0106 |
| 10261 | 292 | 262 | 'July 22, 2026' → 2026-07-22 | '+1 555 945 0125' → (555) 945-0125 |
| 10262 | 122 | 263 | 'July 24, 2026' → 2026-07-24 | '+1 555 745 0100' → (555) 745-0100 |
| 10263 | 135 | 264 | '2026-07-24' → 2026-07-24 | '555-202-0108' → (555) 202-0108 |
| 10264 | 176 | 265 | '2026-07-26' → 2026-07-26 | '+1 555 707 0126' → (555) 707-0126 |
| 10265 | 148 | 266 | 'July 28, 2026' → 2026-07-28 | '555.779.0152' → (555) 779-0152 |
| 10266 | 263 | 267 | '2026-08-04' → 2026-08-04 | '555.522.0120' → (555) 522-0120 |
| 10267 | 53 | 268 | '8/4/26' → 2026-08-04 | '+1 555 988 0103' → (555) 988-0103 |
| 10268 | 27 | 269 | '5-Aug-2026' → 2026-08-05 | '+1 555 484 0105' → (555) 484-0105 |
| 10269 | 184 | 270 | '2062-08-06' → 2026-08-06 | '555.967.0124' → (555) 967-0124 |
| 10270 | 94 | 271 | '7-Aug-2026' → 2026-08-07 | '+1 555 519 0160' → (555) 519-0160 |
| 10271 | 265 | 272 | '11-Aug-2026' → 2026-08-11 | '(555) 404-0118' → (555) 404-0118 |
| 10272 | 62 | 273 | '8/12/26' → 2026-08-12 | '+1 555 141 0112' → (555) 141-0112 |
| 10273 | 117 | 274 | '2026-08-13' → 2026-08-13 | '(555) 829-0101' → (555) 829-0101 |
| 10274 | 153 | 275 | '2026-08-13' → 2026-08-13 | '555-859-0158' → (555) 859-0158 |
| 10275 | 221 | 276 | '2026-08-17' → 2026-08-17 | '(555) 659-0129' → (555) 659-0129 |
| 10276 | 274 | 277 | '8/19/26' → 2026-08-19 | '+1 555 646 0142' → (555) 646-0142 |
| 10277 | 35 | 278 | '8/20/26' → 2026-08-20 | '+1 555 404 0118' → (555) 404-0118 |
| 10278 | 8 | 279 | 'August 23, 2026' → 2026-08-23 | '+1 555 707 0126' → (555) 707-0126 |
| 10279 | 152 | 280 | '8/24/26' → 2026-08-24 | '555.729.0141' → (555) 729-0141 |
| 10280 | 181 | 281 | '2026-08-29' → 2026-08-29 | '(555) 519-0160' → (555) 519-0160 |
| 10281 | 258 | 282 | '8/29/26' → 2026-08-29 | '5552650145' → (555) 265-0145 |
| 10282 | 158,171 | 283 | '2026-08-29' → 2026-08-29 | '5559360168' → (555) 936-0168 |
| 10283 | 14 | 284 | '30-Aug-2026' → 2026-08-30 | '+1 555 967 0124' → (555) 967-0124 |
| 10284 | 57 | 285 | '2026-09-06' → 2026-09-06 | '555-749-0117' → (555) 749-0117 |
| 10285 | 20 | 286 | '7-Sep-2026' → 2026-09-07 | '+1 555 522 0120' → (555) 522-0120 |
| 10286 | 119 | 287 | '2026-09-17' → 2026-09-17 | '555.450.0155' → (555) 450-0155 |
| 10287 | 267 | 288 | '17-Sep-2026' → 2026-09-17 | '555.936.0168' → (555) 936-0168 |
| 10288 | 198 | 289 | '18-Sep-2026' → 2026-09-18 | '555-916-0130' → (555) 916-0130 |
| 10289 | 109 | 290 | '9/22/26' → 2026-09-22 | '+1 555 404 0118' → (555) 404-0118 |
| 10290 | 280 | 291 | '9/23/26' → 2026-09-23 | '555-707-0126' → (555) 707-0126 |
| 10291 | 111 | 292 | '2026-09-23' → 2026-09-23 | '+1 555 368 0131' → (555) 368-0131 |
| 10292 | 38 | 293 | '9/28/26' → 2026-09-28 | '555.265.0145' → (555) 265-0145 |
| 10293 | 233 | 294 | 'September 30, 2026' → 2026-09-30 | '555.151.0102' → (555) 151-0102 |

