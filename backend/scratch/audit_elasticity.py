import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.historical_pricing_baseline import HistoricalPricingBaseline
import json

df = DataPipeline.load_and_process_file(Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx"))
df_feat = FeatureEngineer.process_dataframe(df)
df_feat["booking_date_dt"] = pd.to_datetime(df_feat["booking_date"], errors="coerce")
df_sorted = df_feat.sort_values(by="booking_date_dt").copy()

drop_mask = pd.Series(False, index=df_sorted.index)
if "commercial_slot" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["commercial_slot"] == "Extended Day")
if "is_manual_outlier" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["is_manual_outlier"] == 1)
df_sorted = df_sorted[~drop_mask].copy()

df_sorted = HistoricalPricingBaseline.fit_predict_expanding(df_sorted)

model_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/models_store/champion_model.joblib")
artifact = joblib.load(model_path)
model = artifact["model"]["base_model"]
features = artifact["features"]

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
for f in features:
    if f not in X_full.columns: X_full[f] = 0.0

df_sorted["prediction"] = df_sorted["historical_baseline_price"] + model.predict(X_full[features])
df_sorted["bias"] = df_sorted["prediction"] - df_sorted["selling_price"]

results = []
segments = df_sorted.groupby(["commercial_slot", "month", "is_weekend"])

def calculate_elasticity(base_row, model, features, feature_name, values, base_val):
    preds = []
    for v in values:
        r = base_row.copy()
        r[feature_name] = v
        # recalculate duration_ratio if duration_hours changes
        if feature_name == "duration_hours" and base_row.get("slot_capacity_hours", 1) > 0:
            r["duration_ratio"] = v / base_row.get("slot_capacity_hours", 12)
        preds.append(float(model.predict(pd.DataFrame([r])[features])[0]))
    if len(preds) < 2: return 0.0, False
    diff = preds[-1] - preds[0]
    flatlined = (diff < 10.0) # practically flat
    return diff, flatlined

for (slot, month, weekend), group in segments:
    if len(group) < 3: continue
    
    med = group["selling_price"].median()
    p75 = group["selling_price"].quantile(0.75)
    p90 = group["selling_price"].quantile(0.90)
    pred_mean = group["prediction"].mean()
    bias = group["bias"].mean()
    
    # High-price segment systematic underprediction
    high_price_mask = group["selling_price"] >= p75
    high_bias = group.loc[high_price_mask, "bias"].mean() if sum(high_price_mask) > 0 else 0
    
    # Elasticity checks on a representative row (the median-ish row)
    rep_idx = (group["selling_price"] - med).abs().idxmin()
    rep_row = X_full.loc[rep_idx].copy()
    
    guest_diff, guest_flat = calculate_elasticity(rep_row, model, features, "person_count", [4, 10, 15], 4)
    dur_diff, dur_flat = calculate_elasticity(rep_row, model, features, "duration_hours", [8, 12, 16], 8)
    
    results.append({
        "slot": slot,
        "month": month,
        "weekend": weekend,
        "count": len(group),
        "median_price": med,
        "p75_price": p75,
        "p90_price": p90,
        "predicted_mean": pred_mean,
        "bias": bias,
        "high_price_bias": high_bias,
        "guest_elasticity_15_vs_4": guest_diff,
        "guest_flatlined": guest_flat,
        "dur_elasticity_16_vs_8": dur_diff,
        "dur_flatlined": dur_flat
    })

pd.DataFrame(results).to_csv("scratch/elasticity_audit.csv", index=False)
print("Audit saved to scratch/elasticity_audit.csv")

