# Property Metrics Evaluation Logic Documentation

## Overview
The Property Evaluation Service calculates comprehensive metrics to assess property performance for a given month by comparing actual data (historical bookings and revenue) against expected benchmarks derived from market data and property adjustment factors.

---

## Data Sources & Input Parameters

### 1. **Property Data**
- **property_id**: Unique identifier of the property
- **number_of_rooms**: Number of rooms in the property (default: 1)
- **name**: Property name

### 2. **Daily Property Reports** (Two data types)
#### Actual Data (Historical)
- `data_type = 'actual'`
- Records past bookings and revenue
- Aggregated fields:
  - `stay_over`: Number of nights (room-nights)
  - `total_income`: Revenue generated

#### OTB Data (On-The-Books - Future Bookings)
- `data_type = 'otb'`
- Records confirmed future bookings
- Aggregated fields:
  - `stay_over`: Number of nights (room-nights)
  - `total_income`: Expected future revenue

### 3. **PropertyConfig** (Monthly Configuration)
Thresholds and market inputs stored per property per month:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `market_adr` | Decimal | - | Market Average Daily Rate (benchmark pricing) |
| `market_occupancy` | Float (0-1) | - | Market occupancy rate (0% to 100%) |
| `paf` | Decimal | 1.0 | Property Adjustment Factor (competitive position) |
| `pace_threshold` | Decimal | 0.95 | Revenue pace minimum threshold (95%) |
| `nights_low_threshold` | Decimal | 0.90 | Minimum occupancy pace (90% of expected) |
| `nights_high_threshold` | Decimal | 1.05 | Maximum occupancy pace (105% of expected) |
| `adr_low_threshold` | Decimal | 0.90 | Minimum ADR ratio (90% of expected) |
| `adr_high_threshold` | Decimal | 1.15 | Maximum ADR ratio (115% of expected) |
| `early_month_guard_days` | Integer | 5 | Guard period days (not currently used in evaluation) |

### 4. **Calculated Date Values**
- `current_day`: Today's day of month (min of today.day and days_in_month)
- `days_in_month`: Total days in the evaluated month
- `month`: Format "YYYY-MM"

---

## Calculation Methods

### 1. **Expected Metrics Calculation**
Calculates what the property should achieve based on market benchmarks.

#### Formulas:

```
expected_adr = market_adr × paf
```
Adjusts market ADR by the property's competitive positioning factor.

```
expected_occupancy = market_occupancy
```
Expected occupancy equals market occupancy rate.

```
expected_nights_month = days_in_month × number_of_rooms × expected_occupancy
```
Expected total room-nights for the full month.

```
expected_revenue_month = expected_nights_month × expected_adr
```
Expected total revenue for the full month.

```
expected_nights_td = current_day × number_of_rooms × expected_occupancy
```
Expected room-nights from start of month to today.

```
expected_revenue_td = expected_nights_td × expected_adr
```
Expected revenue from start of month to today (To Date).

#### Returned Values:
```
{
  'expected_adr': float,              # Expected ADR
  'expected_occupancy': float,         # Expected occupancy rate (0-1)
  'expected_nights_month': float,      # Expected room-nights for full month
  'expected_revenue_month': float,     # Expected revenue for full month target
  'expected_nights_td': float,         # Expected room-nights to date
  'expected_revenue_td': float,        # Expected revenue to date (benchmark)
}
```

---

### 2. **Actual Data Aggregation**

#### Actual ADR (To Date):
```
actual_adr_td = actual_revenue_td / actual_nights_td  (if actual_nights_td > 0, else 0)
```
Average Daily Rate based on actual bookings.

#### Actual Nights (To Date):
```
actual_nights_td = Sum of all stay_over from actual data for current month
```
Total room-nights already booked and stayed.

#### Actual Revenue (To Date):
```
actual_revenue_td = Sum of all total_income from actual data for current month
```
Total revenue already generated.

---

### 3. **OTB (On-The-Books) Data Aggregation**

#### OTB Nights:
```
otb_nights = Sum of all stay_over from OTB data for current month
```
Room-nights from confirmed future bookings.

#### OTB Revenue:
```
otb_revenue = Sum of all total_income from OTB data for current month
```
Expected revenue from future bookings.

---

### 4. **KPI Calculations**
Compare actual performance against expected benchmarks using configurable thresholds.

#### Pace Ratio (Revenue):
```
pace_ratio = actual_revenue_td / expected_revenue_td  (if expected_revenue_td > 0, else 0)
```
**Interpretation:**
- `pace_ratio = 1.0`: On pace
- `pace_ratio > 1.0`: Exceeding expectations
- `pace_ratio < 1.0`: Below pace
- **Validation Rule**: `pace_ratio >= pace_threshold` (default: 0.95 or 95%)

#### Nights Pace Ratio:
```
nights_pace_ratio = actual_nights_td / expected_nights_td  (if expected_nights_td > 0, else 0)
```
**Interpretation:** Room-night booking pace vs expected.
- **Validation Rules:**
  - `nights_pace_ratio >= nights_low_threshold` (default: 0.90 or 90%)
  - `nights_pace_ratio <= nights_high_threshold` (default: 1.05 or 105%)

#### ADR Ratio:
```
adr_ratio = actual_adr / expected_adr  (if expected_adr > 0, else 0)
```
**Interpretation:** How actual pricing compares to expected.
- **Validation Rules:**
  - `adr_ratio >= adr_low_threshold` (default: 0.90 or 90%)
  - `adr_ratio <= adr_high_threshold` (default: 1.15 or 115%)

#### ADR Gap:
```
adr_gap = actual_adr - expected_adr
```
**Interpretation:** Dollar difference between actual and expected ADR.
- Positive: Better pricing than expected
- Negative: Lower pricing than expected

#### KPI Output:
```
{
  'pace_ratio': float,                   # Revenue pace ratio
  'pace_ratio_vs_threshold': boolean,    # pace_ratio >= pace_threshold?
  'nights_pace_ratio': float,            # Nights pace ratio
  'nights_pace_vs_low': boolean,         # nights_pace_ratio >= low_threshold?
  'nights_pace_vs_high': boolean,        # nights_pace_ratio <= high_threshold?
  'adr_ratio': float,                    # ADR comparison ratio
  'adr_gap': float,                      # ADR dollar gap
  'adr_vs_low': boolean,                 # adr_ratio >= low_threshold?
  'adr_vs_high': boolean,                # adr_ratio <= high_threshold?
  'actual_adr': float,                   # Actual ADR achieved
}
```

---

### 5. **Forecast & Potential Revenue Calculation**
Projects end-of-month outcomes and identifies revenue upside.

#### Forecast Revenue (Pace + OTB):
```
forecast_revenue = actual_revenue_td + otb_revenue
```
Revenue if all OTB bookings convert (actual + confirmed future).

#### Remaining Free Days:
```
remaining_days = max(0, days_in_month - current_day - otb_nights)
```
Available room-nights not yet occupied or booked.

#### Potential Revenue from Remaining Days:
```
potential_revenue_remaining = remaining_days × number_of_rooms × expected_occupancy × expected_adr
```
Expected revenue opportunity from unbooked periods.

#### Total Potential Revenue:
```
potential_revenue = forecast_revenue + potential_revenue_remaining
```
Maximum achievable revenue if remaining days fill at expected pace.

#### Forecast vs Target (Delta):
```
forecast_vs_target = forecast_revenue - expected_revenue_month
```
**Interpretation:**
- Positive: Exceeding monthly target
- Negative: Below monthly target

#### Forecast vs Target Percentage:
```
forecast_vs_target_pct = (forecast_vs_target / expected_revenue_month) × 100  (if expected_revenue_month > 0, else 0)
```
Percentage variance from monthly revenue target.

#### Forecast Output:
```
{
  'forecast_revenue': float,              # Pace + OTB revenue
  'potential_revenue': float,             # Maximum possible revenue
  'remaining_free_days': float,           # Unbooked room-nights available
  'forecast_vs_target': float,            # Revenue delta from target
  'forecast_vs_target_pct': float,        # Percentage variance (%)
}
```

---

### 6. **Data Validation**
Checks data quality and completeness.

#### Validation Rules:
```
has_revenue_data = (total_revenue is not None AND total_revenue > 0)
```
At least some revenue has been recorded.

```
has_nights_data = (total_nights is not None AND total_nights > 0)
```
At least some nights have been booked.

```
data_valid = has_revenue_data AND has_nights_data
```
Both revenue and night data are present.

#### Validation Output:
```
{
  'has_revenue_data': boolean,    # Revenue data exists?
  'has_nights_data': boolean,     # Night data exists?
  'data_valid': boolean,          # Both revenue and night data valid?
}
```

---

## Complete Evaluation Output Structure

```json
{
  "property_id": "integer",
  "property_name": "string",
  "month": "YYYY-MM",
  "current_day": "integer (1-31)",
  "days_in_month": "integer",
  "rooms": "integer",

  "actual_nights_td": "float (room-nights)",
  "actual_revenue_td": "float ($)",
  "actual_adr_td": "float ($/night)",

  "otb_nights": "float (room-nights)",
  "otb_revenue": "float ($)",

  "expected_adr": "float ($/night)",
  "expected_occupancy": "float (0-1)",
  "expected_nights_month": "float (room-nights)",
  "expected_revenue_month": "float ($)",
  "expected_nights_td": "float (room-nights)",
  "expected_revenue_td": "float ($)",

  "pace_ratio": "float",
  "pace_ratio_vs_threshold": "boolean",
  "nights_pace_ratio": "float",
  "nights_pace_vs_low": "boolean",
  "nights_pace_vs_high": "boolean",
  "adr_ratio": "float",
  "adr_gap": "float ($)",
  "adr_vs_low": "boolean",
  "adr_vs_high": "boolean",
  "actual_adr": "float ($/night)",

  "forecast_revenue": "float ($)",
  "potential_revenue": "float ($)",
  "remaining_free_days": "float (room-nights)",
  "forecast_vs_target": "float ($)",
  "forecast_vs_target_pct": "float (%)",

  "has_revenue_data": "boolean",
  "has_nights_data": "boolean",
  "data_valid": "boolean"
}
```

---

## Evaluation Process Flow

```
1. Load PropertyConfig for property + month
2. Parse month to get calendar info (days_in_month, current_day)
3. Aggregate DailyPropertyReport:
   ├─ Filter by data_type='actual'
   └─ Filter by data_type='otb'
4. Load Property metadata (rooms)

5. Execute Calculations:
   ├─ _calculate_expected_metrics()
   │  └─ Returns expected ADR, occupancy, nights, revenue
   │
   ├─ _calculate_kpis()
   │  ├─ Uses actual data + expected metrics
   │  └─ Returns pace ratios, ADR comparisons, validation booleans
   │
   ├─ _calculate_forecast()
   │  ├─ Uses actual_revenue + otb_revenue + remaining capacity
   │  └─ Returns forecast revenue, potential, variance
   │
   └─ _calculate_validation()
      └─ Returns data quality flags

6. Combine all results into single evaluation dictionary
7. Return complete evaluation output
```

---

## Key Performance Decision Rules

### Revenue Health (Pace Ratio)
| Condition | Status | Action |
|-----------|--------|--------|
| `pace_ratio >= 0.95` | ✅ Healthy | On or exceeding pace |
| `pace_ratio < 0.95` | ⚠️ At Risk | Below pace threshold |
| `pace_ratio > 1.0` | ✅ Strong | Exceeding expectations |

### Occupancy Health (Nights Pace)
| Condition | Status | Action |
|-----------|--------|--------|
| `nights_pace_ratio >= 0.90 AND <= 1.05` | ✅ Healthy | Within acceptable range |
| `nights_pace_ratio < 0.90` | ⚠️ Underbooked | Below occupancy target |
| `nights_pace_ratio > 1.05` | ⚠️ Unusual | Unusually high bookings |

### Pricing Health (ADR Ratio)
| Condition | Status | Action |
|-----------|--------|--------|
| `adr_ratio >= 0.90 AND <= 1.15` | ✅ Healthy | Pricing within range |
| `adr_ratio < 0.90` | ⚠️ Underpriced | Pricing below benchmark |
| `adr_ratio > 1.15` | ⚠️ Overpriced? | Significantly above market |

### Data Quality
| Condition | Status | Action |
|-----------|--------|--------|
| `data_valid = true` | ✅ Valid | Evaluation reliable |
| `data_valid = false` | ❌ Invalid | No actual bookings yet (early month) |

---

## Edge Cases & Defaults

| Scenario | Handling |
|----------|----------|
| `actual_nights_td = 0` | `actual_adr_td = 0` (avoid division by zero) |
| `expected_nights_td = 0` | `nights_pace_ratio = 0` (avoid division by zero) |
| `expected_revenue_td = 0` | `pace_ratio = 0` (avoid division by zero) |
| `expected_adr = 0` | `adr_ratio = 0` (avoid division by zero) |
| `number_of_rooms = null` | Defaults to 1 |
| `current_day > days_in_month` | Capped at `days_in_month` |
| `remaining_days < 0` | Floored at 0 |
| `expected_revenue_month = 0` | `forecast_vs_target_pct = 0` (avoid division by zero) |

---

## Configuration Example

### Typical PropertyConfig Setup
```python
PropertyConfig(
    property=my_property,
    month="2026-03",
    
    # Market Data
    market_adr=150.00,           # $150/night market average
    market_occupancy=0.75,        # 75% market occupancy rate
    paf=0.95,                     # Property underperforming (95% of market)
    
    # Performance Thresholds
    pace_threshold=0.95,          # Must maintain 95% revenue pace
    nights_low_threshold=0.90,    # At least 90% occupancy pace
    nights_high_threshold=1.05,   # Cap unusual overbooking at 105%
    adr_low_threshold=0.90,       # Don't let pricing fall below 90% of expected
    adr_high_threshold=1.15,      # Flag if pricing exceeds 115% of expected
)
```

### Expected Calculations with Example Data
```
market_adr = $150/night
market_occupancy = 75%
paf = 0.95 (property adjusted down 5%)
current_day = 15
days_in_month = 31
rooms = 3

Expected ADR = 150 × 0.95 = $142.50/night
Expected Occupancy = 75%
Expected Nights (Month) = 31 × 3 × 0.75 = 69.75 room-nights
Expected Revenue (Month) = 69.75 × 142.50 = $9,938.75
Expected Nights (To Date) = 15 × 3 × 0.75 = 33.75 room-nights
Expected Revenue (To Date) = 33.75 × 142.50 = $4,809.38

If actual_revenue_td = $5,000:
  pace_ratio = 5000 / 4809.38 = 1.04 (exceeding pace ✅)
```

---

## Summary

The **PropertyEvaluationService** provides a data-driven framework for:
1. **Benchmarking** property performance against market expectations
2. **Monitoring** real-time performance with configurable thresholds
3. **Forecasting** end-of-month outcomes based on current bookings
4. **Identifying** revenue opportunities in remaining inventory
5. **Validating** data quality for reliable decision-making

All calculations use high-precision decimal operations to ensure accurate financial metrics.
