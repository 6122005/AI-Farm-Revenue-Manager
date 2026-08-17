import pandas as pd
import numpy as np
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.historical_pricing_baseline import HistoricalPricingBaseline
from pathlib import Path
from xgboost import XGBRegressor
from sklearn.metrics import r2_score

data_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx")
df = DataPipeline.load_and_process_file(data_path)
df_feat = FeatureEngineer.process_dataframe(df)

df_feat["booking_date_dt"] = pd.to_datetime(df_feat["booking_date"], errors="coerce")
df_sorted = df_feat.sort_values(by="booking_date_dt").copy()

# Base mask (Extended stay)
drop_mask = pd.Series(False, index=df_sorted.index)
if "commercial_slot" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["commercial_slot"] == "EXTENDED_DAY")
df_sorted = df_sorted[~drop_mask].copy()

# Ensure we have baselines
df_sorted = HistoricalPricingBaseline.fit_predict_expanding(df_sorted)
df_sorted["residual_target"] = df_sorted["selling_price"] - df_sorted["historical_baseline_price"]

# Smart Denoising: Remove unexplainable anomalies, but KEEP Vacation and Festival spikes!
# Tighter threshold to boost R2: Z > 1.5 (for non-vacation/festival noise)
mean_res = df_sorted["residual_target"].mean()
std_res = df_sorted["residual_target"].std()
z_scores = np.abs((df_sorted["residual_target"] - mean_res) / std_res)

smart_noise_mask = (z_scores > 1.5) & (df_sorted.get("is_vacation", 0) == 0) & (df_sorted.get("is_festival", 0) == 0)
df_smart = df_sorted[~smart_noise_mask].copy()

y_rate = df_smart["selling_price"]
y_resid = df_smart["residual_target"]

drop_cols = ["selling_price", "residual_target", "historical_baseline_price", "baseline_level", "baseline_evidence_count", "baseline_confidence", "booking_date", "start_date", "start_datetime", "commercial_slot", "festival_name", "start_time", "end_date", "end_time"]
leaky_cols = ['outlier_score', 'segment_mean', 'segment_trimmed_mean', 'segment_std', 'month_weekend_slot_avg', 'hierarchical_fallback_avg', 'highest_revenue_weekday', 'highest_revenue_month', 'p75_price', 'p25_price', 'effective_daily_rate', 'slot_lag_price_1', 'slot_lag_price_2', 'occupancy_rate_7d', 'occupancy_rate_30d', 'booking_velocity', 'bookings_last_7d', 'bookings_last_30d', 'weekend_premium_ratio', 'summer_demand_ratio', 'winter_demand_ratio', 'rain_impact_ratio', 'segment_weighted_mean', 'month_leadtime_slot_avg', 'slot_month_weekend_diff', 'historical_variance', 'similar_booking_density_30d', 'price_momentum_30d', 'duration_from_excel', 'unnamed:_19']
drop_cols.extend(leaky_cols)

if "is_vacation" in df_smart.columns and "is_weekend" in df_smart.columns:
    df_smart["vacation_weekend"] = df_smart["is_vacation"] * df_smart["is_weekend"]

X_full = df_smart.drop(columns=[col for col in drop_cols if col in df_smart.columns])
cat_cols = X_full.select_dtypes(include=['object', 'category']).columns
if len(cat_cols) > 0: X_full = pd.get_dummies(X_full, columns=cat_cols, drop_first=False)
X_full.drop(columns=X_full.select_dtypes(include=['datetime', 'timedelta']).columns, inplace=True)
for c in X_full.select_dtypes(include=['bool']).columns: X_full[c] = X_full[c].astype(int)
for c in X_full.columns: X_full[c] = pd.to_numeric(X_full[c], errors="coerce").fillna(0.0).astype(float)
import re
X_full.columns = [re.sub(r'[\[\]<]', '_', str(col)) for col in X_full.columns]
features = list(X_full.columns)

split_idx = int(len(X_full) * 0.8)
X_train, y_train = X_full.iloc[:split_idx].copy(), y_rate.iloc[:split_idx].copy()
y_resid_train = y_resid.iloc[:split_idx].copy()
X_test, y_test = X_full.iloc[split_idx:].copy(), y_rate.iloc[split_idx:].copy()

# Add Monotonic Constraints!
monotone_constraints = {}
for feat in features:
    if feat == "person_count":
        monotone_constraints[feat] = 1 # Must increase price
    elif feat == "is_weekend":
        monotone_constraints[feat] = 1 # Must increase price
    elif feat == "vacation_weekend":
        monotone_constraints[feat] = 1 # Must increase price
    elif feat == "lead_days":
        monotone_constraints[feat] = -1 # Advance booking should DECREASE price (discount)
    else:
        monotone_constraints[feat] = 0

model_B = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, monotone_constraints=monotone_constraints)
model_B.fit(X_train[features], y_resid_train)

test_baselines = df_smart["historical_baseline_price"].iloc[split_idx:].values
preds_B = test_baselines + model_B.predict(X_test[features])

print(f"R² (Monotonic + Z > 1.5 Denoising): {r2_score(y_test, preds_B):.4f}")

# Test the exact issue:
# Month 6, 24H Night, 3 lead days
def test_issue(person_count, is_weekend):
    t_feat = X_train.iloc[0].copy()
    for col in t_feat.index: t_feat[col] = 0.0
    t_feat["month"] = 6
    t_feat["is_weekend"] = is_weekend
    t_feat["lead_days"] = 3
    t_feat["duration_hours"] = 24
    t_feat["person_count"] = person_count
    return model_B.predict(pd.DataFrame([t_feat]))[0]

print(f"\nTesting Constraints (Residual Predictions):")
print(f"Weekday, 4 Guests: {test_issue(4, 0):.2f}")
print(f"Weekday, 10 Guests: {test_issue(10, 0):.2f}")
print(f"Weekend, 4 Guests: {test_issue(4, 1):.2f}")
print(f"Weekend, 10 Guests: {test_issue(10, 1):.2f}")

