# Problem Statement — Phase 1 (Neutral Discovery)

> **Explicit statement:** "No target variable has been selected, ranked, or proposed in this phase (G1)."
> All problems below are presented as **equal-weight options**. Ranking, narrowing, or target selection
> is deferred to Phase 3 with explicit user approval.

## Business context

The hotel receives ~36,275 bookings (2017–2018) recorded with guest composition, stay length,
lead time, market segment, room type, price, and final booking status (32.8% canceled, 67.2% not canceled).
Cancellations create revenue uncertainty, inventory distortion, and last-minute re-selling pressure.

## Business problems and predictive opportunities (equal-weight options)

### P-A. Booking cancellation risk
- **Description:** anticipate which bookings are likely to be canceled before arrival.
- **Expected business metric to impact:** revenue lost to cancellations; occupancy forecast accuracy.
- **Candidate problem types (preliminary hypothesis, not a decision):** classification.
- **Related variables (descriptive):** `lead_time`, `market_segment_type`, `avg_price_per_room`,
  `no_of_special_requests`, `repeated_guest`, `no_of_previous_cancellations`, arrival date fields.

### P-B. Revenue management and pricing
- **Description:** understand how `avg_price_per_room` relates to booking outcomes and demand patterns
  across segments and seasons.
- **Expected business metric to impact:** RevPAR (revenue per available room); pricing decisions.
- **Candidate problem types (preliminary hypothesis):** regression (price) or descriptive analytics.
- **Related variables (descriptive):** `avg_price_per_room`, `room_type_reserved`, `market_segment_type`,
  `arrival_month`, stay-length fields.

### P-C. Demand seasonality and occupancy planning
- **Description:** characterize monthly/seasonal demand to inform staffing, inventory, and promotion timing.
- **Expected business metric to impact:** occupancy rate; operational cost efficiency.
- **Candidate problem types (preliminary hypothesis):** regression (demand volume) or descriptive analytics.
- **Related variables (descriptive):** `arrival_month`, `arrival_year`, `no_of_week_nights`,
  `no_of_weekend_nights`, `no_of_adults`, `no_of_children`.

### P-D. Guest loyalty and repeat behavior
- **Description:** profile repeat guests and their historical fulfillment (`no_of_previous_bookings_not_canceled`,
  `no_of_previous_cancellations`) to inform loyalty offers.
- **Expected business metric to impact:** repeat-guest share; retention campaign ROI.
- **Candidate problem types (preliminary hypothesis):** classification (repeat-guest propensity) or descriptive analytics.
- **Related variables (descriptive):** `repeated_guest`, `no_of_previous_cancellations`,
  `no_of_previous_bookings_not_canceled`, `market_segment_type`, `no_of_special_requests`.

### P-E. Ancillary services uptake
- **Description:** understand drivers of meal-plan selection and special requests to improve upsell conversion.
- **Expected business metric to impact:** ancillary revenue per booking.
- **Candidate problem types (preliminary hypothesis):** classification (uptake) or descriptive analytics.
- **Related variables (descriptive):** `type_of_meal_plan`, `no_of_special_requests`,
  `no_of_adults`, `avg_price_per_room`, `room_type_reserved`.

## Constraints observed in this phase (G1)

- No problem was ranked as "most relevant".
- No target variable was selected, defined, ranked, or proposed.
- No model was trained.
- Candidate problem types are listed only as preliminary hypotheses.
