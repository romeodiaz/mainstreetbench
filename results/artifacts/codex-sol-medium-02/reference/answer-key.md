# Main Street Bench v0.1: answer key (Corner Loaf Bakery orders)

KEEP THIS OFF SCREEN until the results segment. Never give it to any agent.

File: customer_orders.csv - 300 rows (293 real orders incl. 3 refunds, 3 test rows, 4 duplicate rows). As-of date: 2026-09-30.

## Planted problems (score 1 point each, 12 total)

Issues 05a and 05b count as one point together (emails). Everything else is one point each.

### 01 Same customer, different name spellings

- 10032 (maria lopez = Maria Lopez)
- 10213 (M. Lopez = Maria Lopez)
- 10146 (Lopez, Maria = Maria Lopez)
- 10223 (MARIA LOPEZ = Maria Lopez)
- 10146 (email blank - match Maria Lopez by phone)
- 10208 (james chen = James Chen)
- 10040 (J. Chen = James Chen)
- 10191 (Chen, James = James Chen)
- 10191 (email blank - match James Chen by phone)
- 10052 (priya patel = Priya Patel)
- 10038 (P. Patel = Priya Patel)
- 10052 (email blank - match Priya Patel by phone)

### 02 Extra spaces in customer names

- 10248
- 10224
- 10111
- 10243
- 10119
- 10023
- 10125
- 10259

### 03 Mixed date formats (ISO, M/D/YY, 'March 4, 2026', 4-Mar-2026)

- throughout the file

### 04 Prices stored as text ($, USD)

- 10036
- 10235
- 10080
- 10141
- 10233
- 10051
- 10182
- 10262
- 10175
- 10195
- 10230
- 10009
- 10027
- 10187
- 10171
- 10130
- 10217
- 10073
- 10103
- 10120
- 10286
- 10077
- 10129
- 10256
- 10041
- 10031 (total)
- 10181 (total)

### 05a Missing emails recoverable from other rows

- 10271
- 10183
- 10127
- 10113
- 10069
- 10058
- 10215
- 10047
- 10110
- 10254

### 05b Customers with no email anywhere (flag only)

- 10063
- 10095
- 10222
- 10248

### 06 Product name typos / variants

- 10001 (Sourdogh Loaf = Sourdough Loaf)
- 10289 (sourdough loaf = Sourdough Loaf)
- 10112 (Sourdogh Loaf = Sourdough Loaf)
- 10122 (Croissant Box 6 = Croissant Box (6))
- 10078 (croissant box (6) = Croissant Box (6))
- 10011 (Croissant Box 6 = Croissant Box (6))
- 10136 (Coffee Beans 1 lb = Coffee Beans 1lb)
- 10051 (Cofee Beans 1lb = Coffee Beans 1lb)
- 10045 (Coffee Beans 1 lb = Coffee Beans 1lb)

### 07 Total does not equal Qty x Unit Price

- 10277 (correct total 27.00)
- 10030 (correct total 9.00)
- 10239 (correct total 27.00)
- 10240 (correct total 100.00)

### 08 Inconsistent phone formats

- throughout the file

### 09 Refund rows (negative qty)

- 10048
- 10070
- 10211

### 10 Impossible future date (2062 typo for 2026)

- 10221 (true date 2026-06-04)
- 10269 (true date 2026-08-06)

### 11 Test orders that are not real sales

- 90001
- 90002
- 90003

### 12 Exact duplicate rows (same Order ID twice)

- 10125
- 10282
- 10052
- 10191

## Expected handling

- Refunds count as negative revenue (keep them, don't delete them).
- Test orders and duplicate rows are removed.
- Math errors: recompute Total = Qty x Unit Price and flag the row.
- 2062 dates: correcting to 2026 with a flag, or excluding with a flag, both pass. Silently keeping 2062 fails.
- Customers with no email anywhere: flag them; don't invent an address.

## Correct results

- Unique real customers: 64
- Total net revenue: $14,196.00 (if the two 2062 rows are excluded instead: $14,175.00)

### Revenue by month

| Month | Net revenue |
| --- | --- |
| 2025-10 | $1,914.00 |
| 2025-11 | $1,915.00 |
| 2025-12 | $1,297.00 |
| 2026-01 | $1,179.00 |
| 2026-02 | $1,046.00 |
| 2026-03 | $1,176.00 |
| 2026-04 | $1,066.00 |
| 2026-05 | $579.00 |
| 2026-06 | $1,395.00 |
| 2026-07 | $1,466.00 |
| 2026-08 | $761.00 |
| 2026-09 | $402.00 |

### Top 10 customers by net revenue

| Rank | Customer | Net revenue |
| --- | --- | --- |
| 1 | Maria Lopez | $834.00 |
| 2 | Daniel Price | $697.00 |
| 3 | Tessa Park | $659.00 |
| 4 | Lena Park | $549.00 |
| 5 | Ahmed Ali | $538.00 |
| 6 | Tariq Levi | $495.00 |
| 7 | Lily Russo | $494.00 |
| 8 | James Chen | $455.00 |
| 9 | Diego Stein | $445.00 |
| 10 | Samuel Farouk | $435.00 |

### Products

| Product | Units (net) | Net revenue |
| --- | --- | --- |
| Croissant Box (6) | 201 | $4,221.00 |
| Coffee Beans 1lb | 148 | $2,664.00 |
| Gift Card | 87 | $2,175.00 |
| Catering Tray | 18 | $2,160.00 |
| Sourdough Loaf | 208 | $1,872.00 |
| Birthday Cake | 23 | $1,104.00 |

### Lapsed customers (no order since 2026-07-02): 32

| Customer | Last order |
| --- | --- |
| Gideon Petrov | 2025-11-13 |
| Tariq Levi | 2025-11-26 |
| Zara Lang | 2025-11-26 |
| Carlos Lopez | 2025-12-06 |
| Arjun Evans | 2025-12-08 |
| Lena Reed | 2025-12-13 |
| Nadia Stein | 2025-12-21 |
| Samuel Farouk | 2025-12-23 |
| Felix Price | 2026-01-06 |
| Luis Novak | 2026-01-09 |
| Owen Morgan | 2026-01-14 |
| Mei Rahman | 2026-01-14 |
| Owen Patel | 2026-01-16 |
| Hannah Moreau | 2026-02-07 |
| Jade Garcia | 2026-02-24 |
| Elena Rahman | 2026-02-24 |
| Lily Russo | 2026-03-03 |
| Mei Ortiz | 2026-03-15 |
| Omar Hart | 2026-03-20 |
| Iris Grant | 2026-03-30 |
| Ravi Russo | 2026-03-30 |
| Elena Moreau | 2026-04-04 |
| Alice Patel | 2026-04-10 |
| Kwame Lang | 2026-04-17 |
| Ahmed Ali | 2026-04-21 |
| Hugo Stone | 2026-04-25 |
| Daniel Nguyen | 2026-05-06 |
| Mei Weber | 2026-05-28 |
| Isaac Obi | 2026-05-30 |
| Amara Holm | 2026-06-09 |
| Ruth Fischer | 2026-06-19 |
| Fatima Obi | 2026-06-21 |
