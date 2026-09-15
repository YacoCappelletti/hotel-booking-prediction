# Business Analysis Report

Purpose: understand and quantify the business value extractable from the hotel reservations dataset
through data-backed insights. All insights are justified with code (`/scripts/p2_q0*.py`),
outputs (`/docs/snippets/`), metrics (`/docs/json/`), and charts (`/docs/images/`).

## Executive summary

- **The problem is large:** 32.8% of 36,275 bookings cancel, putting **EUR 4.30M (37.9%) of the
  EUR 11.35M potential revenue at risk** (Q01).
- **Lead time is the dominant behavioral driver:** cancellation rate climbs monotonically from
  9.9% (bookings 1–7 days ahead) to **73.9%** (bookings 181+ days ahead) (Q02).
- **Channel risk is concentrated:** Online bookings are 64% of volume *and* the highest-risk paying
  segment (36.5% cancellation); Corporate is ~3x safer (10.9%) (Q03).
- **Losses are seasonal:** the top-3 arrival months concentrate **43.2%** of all lost revenue (Q04).
- **Engagement is protective:** 0 special requests → 43.2% cancellation; 3+ → 0%. Repeated guests
  cancel at 1.7% vs 33.6% for new guests (Q05).

## Detailed insights

### Insight 1 — Size of the problem (Q01)

| Metric | Value |
| --- | --- |
| Total bookings | 36,275 |
| Cancellations | 11,881 (32.76%) |
| Total potential revenue | EUR 11.35M |
| Lost revenue | EUR 4.30M (37.9%) |
| Average booking value | ~EUR 313 |

**Recommended action:** integrate a cancellation-risk score into the reservation workflow,
prioritizing high-value, long-lead bookings.

### Insight 2 — Lead time (Q02)

| Lead-time band | Cancel rate | n |
| --- | --- | --- |
| 1–7d | 9.9% | 4,504 |
| 8–30d | 18.9% | 6,610 |
| 31–60d | 23.5% | 6,307 |
| 61–90d | 27.8% | 4,508 |
| 91–180d | 44.9% | 7,772 |
| 181–443d | 73.9% | 5,277 |

Correlation (lead_time, cancel): **0.439**.

**Recommended action:** tiered reconfirmation by band; deposits/non-refundable options for 180+ days.

### Insight 3 — Market segments (Q03)

| Segment | Cancel rate | n | Avg price (EUR) |
| --- | --- | --- | --- |
| Online | 36.5% | 23,214 | ~110 |
| Offline | 29.9% | 10,528 | ~97 |
| Aviation | 29.6% | 125 | ~101 |
| Corporate | 10.9% | 2,017 | ~89 |
| Complementary | 0.0% | 391 | ~0 |

**Recommended action:** partial prepayment or stricter cancellation windows for online; grow
corporate mix in high season.

### Insight 4 — Seasonal revenue exposure (Q04)

Total lost revenue EUR 4.30M; top-3 loss months = 43.2% of the loss, coinciding with peak
volume months (Aug–Oct) with elevated cancellation rates.

**Recommended action:** stricter terms + overbooking buffers in peak months; retention campaigns
ahead of them.

### Insight 5 — Engagement and loyalty (Q05)

| Signal | Cancel rate |
| --- | --- |
| 0 special requests | 43.2% |
| 1 request | 23.8% |
| 2 requests | 14.6% |
| 3+ requests | 0% |
| New guest | 33.6% |
| Repeated guest | 1.7% |

**Recommended action:** nudge guests to add preferences at booking; prioritize zero-request,
first-time, long-lead bookings for reconfirmation.

## Operational translation — `configs/business_rules.json`

The insights above were translated into risk bands, recommendations, and a cost matrix:

- **Low risk (below the model's cost-optimal threshold):** no action — consistent with low-risk profiles observed in Q02/Q03/Q05.
- **Medium risk (0.25–0.55):** proactive reconfirmation + flexible-date incentive — matches the
  28–45% observed rates of mid-horizon/online profiles.
- **High risk (> 0.55):** immediate retention workflow (personal contact, deposit enforcement,
  inventory reallocation) — matches the ~74% observed rate of long-lead zero-engagement profiles.
- **Cost matrix (FN:FP = 10:1):** a missed cancellation costs the booking revenue (~EUR 313 avg);
  an unnecessary retention action costs a small incentive. Exact values are documented as
  assumptions pending finance validation.

## From analysis to prediction

These findings motivated building a cancellation-risk classifier: the target is `booking_status`
(Canceled vs Not_Canceled), and the score from that model feeds the risk bands above. See
`docs/problem_statement.md` and `docs/model_report.md`.
