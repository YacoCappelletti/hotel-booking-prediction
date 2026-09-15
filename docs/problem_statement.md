# Problem Statement

## Business context

The hotel receives ~36,275 bookings (2017–2018) recorded with guest composition, stay length,
lead time, market segment, room type, price, and final booking status (32.8% canceled, 67.2% not canceled).
Cancellations create revenue uncertainty, inventory distortion, and last-minute re-selling pressure.

## Business problems and predictive opportunities

Five problems were analyzed during the business analysis (`docs/business_analysis_report.md`).
The selected one is P-A; the others remain documented as future opportunities.

### P-A. Booking cancellation risk (selected)

- **Description:** anticipate which bookings are likely to be canceled before arrival.
- **Expected business metric to impact:** revenue lost to cancellations; occupancy forecast accuracy.
- **Problem type:** binary classification on `booking_status` (Canceled vs Not_Canceled).
- **Related variables:** `lead_time`, `market_segment_type`, `avg_price_per_room`,
  `no_of_special_requests`, `repeated_guest`, `no_of_previous_cancellations`, arrival date fields.

### P-B. Revenue management and pricing

- **Description:** understand how `avg_price_per_room` relates to booking outcomes and demand patterns
  across segments and seasons.
- **Expected business metric to impact:** RevPAR (revenue per available room); pricing decisions.
- **Candidate problem types:** regression (price) or descriptive analytics.

### P-C. Demand seasonality and occupancy planning

- **Description:** characterize monthly/seasonal demand to inform staffing, inventory, and promotion timing.
- **Expected business metric to impact:** occupancy rate; operational cost efficiency.
- **Candidate problem types:** regression (demand volume) or descriptive analytics.

### P-D. Guest loyalty and repeat behavior

- **Description:** profile repeat guests and their historical fulfillment (`no_of_previous_bookings_not_canceled`,
  `no_of_previous_cancellations`) to inform loyalty offers.
- **Expected business metric to impact:** repeat-guest share; retention campaign ROI.
- **Candidate problem types:** classification (repeat-guest propensity) or descriptive analytics.

### P-E. Ancillary services uptake

- **Description:** understand drivers of meal-plan selection and special requests to improve upsell conversion.
- **Expected business metric to impact:** ancillary revenue per booking.
- **Candidate problem types:** classification (uptake) or descriptive analytics.

## Why P-A first

- It has the largest measured financial exposure: EUR 4.30M of potential revenue at risk (Q01).
- The dominant drivers (lead time, engagement signals, segment) are all collected at booking time,
  so predictions are actionable while the guest can still be retained.
- The response to a prediction is operationally cheap and graded (reconfirmation → deposit),
  making the value of even an imprecise model immediate.
