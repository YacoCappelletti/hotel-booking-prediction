# Business Questions

## 10 candidate business questions (all answerable with the dataset)

1. What is the overall cancellation rate and how much revenue is at risk?
2. How does lead time affect cancellation probability?
3. How do market segments differ in cancellation behavior?
4. What is the revenue impact of cancellations by arrival month?
5. Do engagement and loyalty signals (special requests, repeated guest, history) reduce cancellations?
6. How does average room price vary by room type and segment, and does price relate to cancellations?
7. Does stay length (week vs weekend nights) relate to cancellation behavior?
8. How does demand vary by month and year (seasonality of booking volume)?
9. Does previous cancellation history predict future cancellation behavior?
10. What is the profile of bookings with 0 nights or 0 guests (data anomalies with operational cost)?

## Selected 5 questions (by business impact, feasibility, actionability)

| # | Question | Why selected |
| --- | --- | --- |
| 1 | Overall cancellation rate and revenue at risk | Quantifies the size of the problem in money (EUR 4.30M at risk, 37.9% of potential revenue) — the baseline every other analysis builds on. |
| 2 | Lead time vs cancellation | Strongest single behavioral signal (corr 0.44; 10% → 74% across bands) and directly actionable: intervention policies can be tiered by booking horizon. |
| 3 | Market segment behavior | Channel-risk concentration (Online 64% of volume, ~37% cancellation) enables channel-specific commercial policies. |
| 4 | Revenue impact by month | Converts cancellation behavior into seasonal financial exposure — tells the business *when* to act. |
| 5 | Engagement and loyalty signals | Special requests and repeat-guest flags are collected at booking time, cheap to use, and highly protective (43% → 0%; 1.7% vs 33.6%). |

## Justification of the selection

- **Business impact:** Q1 and Q4 measure the problem directly in EUR; Q2/Q3/Q5 identify the highest-leverage levers.
- **Feasibility:** all five are answerable with existing columns, no external data required.
- **Actionability:** each yields a concrete operational action (tiered reconfirmation, channel policies, seasonal buffers, engagement nudges).

