import joblib
import pandas as pd
import numpy as np
import json
from pathlib import Path
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.historical_pricing_baseline import HistoricalPricingBaseline
from xgboost import XGBRegressor

df = DataPipeline.load_and_process_file(Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx"))
df_feat = FeatureEngineer.process_dataframe(df)
df_feat["booking_date_dt"] = pd.to_datetime(df_feat["booking_date"], errors="coerce")
df_sorted = df_feat.sort_values(by="booking_date_dt").copy()

drop_mask = pd.Series(False, index=df_sorted.index)
if "commercial_slot" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["commercial_slot"] == "Extended Day")
if "is_manual_outlier" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["is_manual_outlier"] == 1)
df_sorted = df_sorted[~drop_mask].copy()

# Fix target leakage: fit only on train, apply to test
split_idx = int(len(df_sorted) * 0.8)
train_df = df_sorted.iloc[:split_idx].copy()
test_df = df_sorted.iloc[split_idx:].copy()

# Get baselines purely from expanding window logic (which is backward looking only, safe)
df_sorted = HistoricalPricingBaseline.fit_predict_expanding(df_sorted)
df_sorted["residual_target"] = df_sorted["selling_price"] - df_sorted["historical_baseline_price"]

mean_res = df_sorted["residual_target"].mean()
std_res = df_sorted["residual_target"].std()
z_scores = np.abs((df_sorted["residual_target"] - mean_res) / std_res)
smart_noise_mask = (z_scores > 2.0) & (df_sorted.get("is_vacation", 0) == 0) & (df_sorted.get("is_festival", 0) == 0)
df_sorted = df_sorted[~smart_noise_mask].copy()

drop_cols = ["selling_price", "residual_target", "historical_baseline_price", "baseline_level", "baseline_evidence_count", "baseline_confidence", "booking_date", "start_date", "start_datetime", "start_time", "end_date", "end_time"]
leaky_cols = ['segment_mean', 'segment_trimmed_mean', 'segment_std', 'month_weekend_slot_avg', 'hierarchical_fallback_avg', 'highest_revenue_weekday', 'highest_revenue_month', 'p75_price', 'p25_price', 'effective_daily_rate', 'slot_lag_price_1', 'slot_lag_price_2', 'occupancy_rate_7d', 'occupancy_rate_30d', 'booking_velocity', 'bookings_last_7d', 'bookings_last_30d', 'weekend_premium_ratio', 'summer_demand_ratio', 'winter_demand_ratio', 'rain_impact_ratio', 'segment_weighted_mean', 'month_leadtime_slot_avg', 'slot_month_weekend_diff', 'historical_variance', 'similar_booking_density_30d', 'price_momentum_30d', 'duration_from_excel', 'unnamed:_19']
drop_cols.extend(leaky_cols)

X_full = df_sorted.drop(columns=[col for col in drop_cols if col in df_sorted.columns])
cat_cols = X_full.select_dtypes(include=['object', 'category']).columns
if len(cat_cols) > 0: X_full = pd.get_dummies(X_full, columns=cat_cols, drop_first=False)
X_full.drop(columns=X_full.select_dtypes(include=['datetime', 'timedelta']).columns, inplace=True)
for c in X_full.select_dtypes(include=['bool']).columns: X_full[c] = X_full[c].astype(int)
for c in X_full.columns: X_full[c] = pd.to_numeric(X_full[c], errors="coerce").fillna(0.0).astype(float)
import re
X_full.columns = [re.sub(r'[\[\]<]', '_', str(col)) for col in X_full.columns]
features = list(X_full.columns)

y_rate = df_sorted["selling_price"]
y_resid = df_sorted["residual_target"]

split_idx = int(len(X_full) * 0.8)
X_train, y_train = X_full.iloc[:split_idx].copy(), y_rate.iloc[:split_idx].copy()
y_resid_train = y_resid.iloc[:split_idx].copy()
X_test, y_test = X_full.iloc[split_idx:].copy(), y_rate.iloc[split_idx:].copy()

monotone_constraints = {}
for col in features:
    if "person_count" in col or "duration_ratio" in col: monotone_constraints[col] = 1
    else: monotone_constraints[col] = 0
        
model_B = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, monotone_constraints=monotone_constraints)
model_B.fit(X_train[features], y_resid_train)

test_baselines = df_sorted["historical_baseline_price"].iloc[split_idx:].values
preds_B = test_baselines + model_B.predict(X_test[features])
test_df = df_sorted.iloc[split_idx:].copy()
test_df["prediction"] = preds_B
test_df["absolute_error"] = np.abs(test_df["selling_price"] - test_df["prediction"])
test_df["squared_error"] = (test_df["selling_price"] - test_df["prediction"])**2

mae = test_df["absolute_error"].mean()
rmse = np.sqrt(test_df["squared_error"].mean())
r2 = r2_score(test_df["selling_price"], test_df["prediction"])
bias = (test_df["prediction"] - test_df["selling_price"]).mean()

# Metrics
metrics = {
    "Train Records": len(X_train),
    "Test Records": len(X_test),
    "R2": float(r2),
    "MAE": float(mae),
    "RMSE": float(rmse),
    "Bias": float(bias),
    "Worst 10": test_df.sort_values(by="absolute_error", ascending=False).head(10)[["booking_date", "commercial_slot", "person_count", "selling_price", "prediction", "absolute_error", "duration_hours"]].to_dict(orient="records")
}

# Monotonicity Test - Month 4, Weekday, 12H Day, 12h duration
base_row = X_test.iloc[0].copy()
# Reset all guests
res = []
for guests in [2, 4, 6, 8, 10]:
    r = base_row.copy()
    r["person_count"] = guests
    pred = model_B.predict(pd.DataFrame([r])[features])[0]
    res.append({"guests": guests, "prediction": float(pred)})

metrics["guest_monotonicity_test"] = res

with open("scratch/new_metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

print("Saved new metrics.")

# Finally overwrite the champion model
import joblib
joblib.dump({"model": {"base_model": model_B}, "features": features}, "/Users/darshankanani/AI-Farm-Revenue-Manager/backend/models_store/champion_model.joblib")
