# ROOT CAUSE REPORT: Model Evaluation Discrepancy (₹330 vs ₹7264 MAE)

## 1. Root Cause Identification
The massive discrepancy between the offline evaluation (MAE ₹330) and the historical replay / online prediction (MAE ₹7264) is caused by a **complete collapse of the feature vector during inference.** 

Specifically, during online prediction, the `FeatureEngineer.process_dataframe()` method is called with a single-row DataFrame. Because it lacks the correct historical context integration logic for single-row inference, two catastrophic failures occur:
1. **Time-Series Rolling Features Fail:** Operations like `.shift(1)` or `.rolling(7d)` on a 1-row DataFrame evaluate to `NaN` and default to `0.0`.
2. **Leave-One-Out (LOO) Hierarchical Features Fail:** The LOO target encoder calculates group averages by taking `(total_sum - current_val) / (total_count - 1)`. For a 1-row DataFrame, `total_count` is 1, causing a division by zero. The system catches this and applies the hardcoded fallback value of `8500.0`.

As a result, the model receives `0.0` for all lag/velocity features and `8500.0` for all hierarchical encodings, causing the XGBoost model to output an inaccurate prediction.

## 2. Evidence
The forensic trace executed across 30 random bookings reveals massive feature divergence for the exact same booking. 

**Example Booking: 2025-11-14 (24H Day)**
* **Offline Transformed Input:** `month_slot_avg` = 15707.3 | `rolling_price_mean_30` = 15176.25 | `booking_velocity` = 0.428
* **Online Transformed Input:** `month_slot_avg` = 8500.0 | `rolling_price_mean_30` = 0.0 | `booking_velocity` = 0.0

Due to this feature wipeout, the model predicted `8.322` instead of `9.719`. When passed through `np.expm1()`, the final price became **₹4,115 instead of ₹16,633**.

## 3. Affected Files and Functions
* **File:** `app/services/feature_engineering.py`
  * **Function:** `process_dataframe()`
  * **Logic:** The `historical_df` parameter is passed into this function, but it is never concatenated with the incoming `df` prior to calculating LOO averages and advanced time-series features.
  * **Logic:** The `_is_prediction_row` marker is never injected into `df`, causing the LOO engine to treat the row as a full dataset of length 1.
* **File:** `app/services/prediction_engine.py`
  * **Function:** `_predict_single_slot()`
  * **Logic:** It passes `historical_df=hist_df` to `FeatureEngineer.process_dataframe`, expecting the engineer to calculate the rolling context correctly, but the feature engineer drops the context.

## 4. Severity
**CRITICAL (P0)**. The shadow ML engine is currently predicting garbage values for every production request. If this had been promoted out of Shadow Mode, the business would have suffered massive revenue loss by severely underpricing high-demand slots (e.g., predicting ₹4,115 for a ₹16,633 slot).

## 5. Recommended Fix
Do **NOT** retrain the model. The model weights are correct. The fix is strictly an inference pipeline bug in `FeatureEngineer.process_dataframe()`.

**Proposed Fix in `FeatureEngineer.process_dataframe()`:**
1. If `historical_df` is provided, assign `df["_is_prediction_row"] = True` and `historical_df["_is_prediction_row"] = False`.
2. Concatenate `historical_df` and `df` at the **very beginning** of the function.
3. Sort the combined DataFrame chronologically by `booking_date`.
4. Run all feature extraction (LOO encodings, time-series shifts, rolling windows) on this combined DataFrame.
5. At the very end of the function, filter the DataFrame back down: `df = combined_df[combined_df["_is_prediction_row"] == True].drop(columns=["_is_prediction_row"])` and return it.

## 6. Confidence Level
**100%**. The mathematical mapping of the missing features perfectly correlates with the exact fallback defaults (`8500.0` and `0.0`) found in the codebase.
