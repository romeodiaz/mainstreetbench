# Sol medium — v0.5 attempt 1, regraded

The [original v0.5 record](sol-medium-v0.5-01.md) stands as recorded: raw score **1.3/100** under grader `bee5fa0`. That grade measured the test driver, not the site.

This regrade runs the same frozen submission, unchanged, under grader `d003be4`. That grader fixes four driver problems the submission exposed:

1. Sol's menu asks for the pickup day before items can be added; the old shopper always added first.
2. Sol disables "Place order" for an invalid or empty gift card; the old shopper treated that as a crash rather than a refusal.
3. Sol removes cart lines with a Remove button, and its quantity box doesn't accept 0; the old shopper typed 0.
4. Sol caps quantities at what's left rather than refusing the order. The daily-limit tests now check that the limit is never exceeded, which is what ticket 3 asks for, instead of requiring a refusal.

The emptied-cart test also no longer passes when nothing was added.

| Check | Passed / total | Score |
|---|---:|---:|
| **Score** | | **97.2/100** |
| Regression: existing behavior | 7/7 | 100 |
| Ticket 1: tax and coupons | 5/5 | 100 |
| Ticket 2: pickup times | 8/8 | 100 |
| Ticket 3: daily limits | 6/6 | 100 |
| Ticket 4: gift cards | 9/10 | 90 |
| Ticket 5: online cancellation | 7/8 | 87.5 |
| Ticket 6: sold out on the menu | 4/4 | 100 |
| Ticket 7: change the cart | 4/4 | 100 |
| Ticket 8: total before ordering | 5/5 | 100 |

## The two failures

Both are real, and both are the same security mistake: the public order page reveals secrets that only the customer's private link should.

- **Strangers can read gift card codes.** `/order/<id>` shows gift card codes to anyone who types an order number, and order numbers count up from 1.
- **Strangers can cancel any order.** The server checks a cancel token, but the public order page puts that token in the Cancel button (`data-token`), and the order JSON includes `cancel_token`. Anyone who opens `/order/<id>` can cancel the order.

## Controls under the same grader

| Site | Score |
|---|---:|
| Reference solution | 100 |
| Untouched starter | 0 (regression 7/7) |
| Alternate UI: radio-button times, +/− cart buttons, 16-digit gift cards | 100 |

Reports: [submission](sol-medium-v0.5-01/regrade/submission-report.json) · [reference](sol-medium-v0.5-01/regrade/control-reference-report.json) · [starter](sol-medium-v0.5-01/regrade/control-starter-report.json) · [alternate UI](sol-medium-v0.5-01/regrade/control-variant5-report.json).

This grade ran on Linux with Playwright for Python and the preinstalled Chromium 141. It ran without the macOS deny-default sandbox used for the original grade, so treat it as a diagnostic regrade until it's repeated under that sandbox.
