# Pipeline Trace for Booking: 2025-11-14 (24H Day)

## Input
```json
{
    "start_datetime": "2025-11-14 10:00",
    "end_datetime": "2025-11-14 22:00",
    "booking_date": "2025-11-14",
    "commercial_slot": "24H Day",
    "person_count": 10,
    "lead_days": 7
}
```

## Feature Engineering Comparison (Offline vs Replay)

| Feature | Offline (Training) | Online (Inference/Replay) | Reason for Mismatch |
|---------|-------------------|--------------------------|---------------------|
| `competitor_price` | 13330.0 | 0.0 | Request object defaults competitor_price to 0.0 |
| `month_slot_avg` | 15707.3 | 8500.0 | LOO logic computes (total - 1), but total=1, resulting in fallback 8500 |
| `month_weekend_slot_avg`| 15707.3 | 8500.0 | Same LOO fallback logic |
| `slot_lag_price_1` | 14420.0 | 0.0 | `.shift(1)` on a single-row dataframe yields NaN -> 0.0 |
| `rolling_price_mean_30` | 15176.25 | 0.0 | `.rolling()` on a single row yields NaN -> 0.0 |
| `booking_velocity` | 0.428 | 0.0 | Rolling occupancy calculation fails on single row |

## ML Prediction
- **Offline Transformed Output:** 9.719
- **Online Transformed Output:** 8.322
- **Offline Final Price:** ₹16,633 (calculated as `np.expm1(9.719)`)
- **Online Final Price:** ₹4,115 (calculated as `np.expm1(8.322)`)

## Business Rules & Commercial Layer
- During Replay, `PredictionEngine` passes the ML prediction through:
  1. **Calibration Check:** (ML vs RAG median bounds)
  2. **Inventory Constraints**
  3. **Output format:** Final price is mapped to `shadow_ml_price`.

## Summary
The pipeline trace confirms that the ML model is receiving a severely degraded feature vector during online inference. All historical context (rolling features) and hierarchical encodings (LOO features) are lost and replaced with fallback values (`0.0` or `8500.0`).
