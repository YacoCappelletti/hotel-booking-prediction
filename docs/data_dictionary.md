# Data Dictionary

**Dataset:** `hotel_reservations.csv` — 36,275 rows x 19 columns

> Note: the `candidate_target` column is a **factual flag only** (rule G1).
> No target evaluation, ranking, or selection is performed in Phase 1.

| Name | Type | Description | Possible values | Missing | Unique | Example | Usable as feature | Candidate target (factual) | Leakage | PII | Temporal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `Booking_ID` | str | Unique booking identifier. | INN##### (unique per row) | 0 | 36,275 | INN00001, INN00002 | no | no | no | no | no |
| `no_of_adults` | int64 | Number of adults in the booking. | 0-4 (int) | 0 | 5 | 2, 1 | yes | no | no | no | no |
| `no_of_children` | int64 | Number of children in the booking. | 0-10 (int; values 9-10 are rare, likely entry errors) | 0 | 6 | 0, 2 | yes | no | no | no | no |
| `no_of_weekend_nights` | int64 | Number of weekend nights (Saturday/Sunday) booked. | 0-7 (int) | 0 | 8 | 1, 2 | yes | no | no | no | no |
| `no_of_week_nights` | int64 | Number of week nights (Monday-Friday) booked. | 0-17 (int) | 0 | 18 | 2, 3 | yes | no | no | no | no |
| `type_of_meal_plan` | str | Meal plan selected by the guest. | Meal Plan 1, Meal Plan 2, Meal Plan 3, Not Selected | 0 | 4 | Meal Plan 1, Not Selected | yes | no | no | no | no |
| `required_car_parking_space` | int64 | Whether the guest requires a parking space (0/1). | 0, 1 | 0 | 2 | 0, 1 | yes | no | no | no | no |
| `room_type_reserved` | str | Room type reserved by the guest (anonymized categories). | Room_Type 1..7 | 0 | 7 | Room_Type 1, Room_Type 4 | yes | no | no | no | no |
| `lead_time` | int64 | Days between booking date and arrival date. | 0-443 (int) | 0 | 352 | 224, 5 | yes | no | no | no | conditional (derived from an implicit booking date; the booking date itself is not in the data) |
| `arrival_year` | int64 | Year of arrival. | 2017, 2018 | 0 | 2 | 2017, 2018 | conditional | no | no | no | yes |
| `arrival_month` | int64 | Month of arrival (1-12). | 1-12 (int) | 0 | 12 | 10, 11 | yes | no | no | no | yes |
| `arrival_date` | int64 | Day of month of arrival (1-31). | 1-31 (int) | 0 | 31 | 2, 6 | yes | no | no | no | yes |
| `market_segment_type` | str | Market segment designation of the booking. | Online, Offline, Corporate, Complementary, Aviation | 0 | 5 | Offline, Online | yes | no | no | no | no |
| `repeated_guest` | int64 | Whether the guest is a repeat customer (0/1). | 0, 1 | 0 | 2 | 0, 1 | yes | no | conditional | no | no |
| `no_of_previous_cancellations` | int64 | Number of previous bookings canceled by this guest. | 0-13 (int) | 0 | 9 | 0, 3 | yes | no | conditional | no | no |
| `no_of_previous_bookings_not_canceled` | int64 | Number of previous bookings not canceled by this guest. | 0-58 (int) | 0 | 59 | 0, 5 | yes | no | conditional | no | no |
| `avg_price_per_room` | float64 | Average price per day of the reservation (EUR). | 0-540 (float; 0 for complementary stays) | 0 | 3,930 | 65.0, 106.68 | yes | no | no | no | no |
| `no_of_special_requests` | int64 | Number of special requests made by the guest (e.g., high floor, view). | 0-5 (int) | 0 | 6 | 0, 1 | yes | no | no | no | no |
| `booking_status` | str | Final status of the booking: Canceled or Not_Canceled. | Canceled, Not_Canceled | 0 | 2 | Not_Canceled, Canceled | no (outcome label) | yes (factual flag only — evaluation deferred to Phase 3) | n/a | no | no |

## Business meaning per column

- **`Booking_ID`** — Traceability key for each reservation record.
- **`no_of_adults`** — Party size; drives room allocation and pricing.
- **`no_of_children`** — Party composition; family segment indicator.
- **`no_of_weekend_nights`** — Stay length component; leisure-travel indicator.
- **`no_of_week_nights`** — Stay length component; business-travel indicator.
- **`type_of_meal_plan`** — Ancillary spend and commitment signal.
- **`required_car_parking_space`** — Arrival-mode proxy; commitment signal.
- **`room_type_reserved`** — Product mix and price-tier proxy.
- **`lead_time`** — Planning horizon; strong behavioral driver of cancellations.
- **`arrival_year`** — Temporal context for seasonality and trend analysis.
- **`arrival_month`** — Seasonality driver for demand and cancellations.
- **`arrival_date`** — Fine-grained timing; combined with year/month gives arrival day.
- **`market_segment_type`** — Channel strategy; different segments show different cancellation behavior.
- **`repeated_guest`** — Loyalty signal; repeat guests behave differently.
- **`no_of_previous_cancellations`** — Guest cancellation history; behavioral risk signal.
- **`no_of_previous_bookings_not_canceled`** — Guest fulfillment history; reliability signal.
- **`avg_price_per_room`** — Price sensitivity driver; direct revenue input.
- **`no_of_special_requests`** — Engagement/commitment signal.
- **`booking_status`** — Outcome of the reservation lifecycle; measures realized revenue loss when Canceled.

## PII / sensitive columns

- `Booking_ID`: pseudonymous identifier — keep as key, exclude from features.
- No direct PII (names, emails, phones, payments, nationality) present.

## Temporal columns

- `arrival_year`, `arrival_month`, `arrival_date`: arrival date components (temporal).
- `lead_time`: derived temporal feature (days between booking and arrival).
- No booking-creation timestamp exists in the dataset.
