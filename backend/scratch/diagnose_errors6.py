import pandas as pd
import numpy as np
import joblib
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.historical_pricing_baseline import HistoricalPricingBaseline
from app.config import MODELS_DIR
from pathlib import Path

# Load Data
data_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx")
df = DataPipeline.load_and_process_file(data_path)
df_feat = FeatureEngineer.process_dataframe(df)

# Filtering just like train_and_select_champion
df_feat["booking_date_dt"] = pd.to_datetime(df_feat["booking_date"], errors="coerce")
df_sorted = df_feat.sort_values(by="booking_date_dt").copy()
drop_mask = pd.Series(False, index=df_sorted.index)
if "is_festival" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["is_festival"] == 1)
if "commercial_slot" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["commercial_slot"] == "EXTENDED_DAY")
df_sorted = df_sorted[~drop_mask].copy()

# Add Baseline
df_sorted = HistoricalPricingBaseline.fit_predict_expanding(df_sorted)

# Load Model
artifact = joblib.load(MODELS_DIR / "champion_model.joblib")
model_B = artifact["model"]["base_model"]
features = artifact["features"]

# Prepare X
drop_cols = ["selling_price", "residual_target", "historical_baseline_price", "baseline_level", "baseline_evidence_count", "baseline_confidence", "booking_date", "start_date", "start_datetime", "commercial_slot", "festival_name", "start_time", "end_date", "end_time", "person_count", "lead_days"]
leaky_cols = ['outlier_score', 'segment_mean', 'segment_trimmed_mean', 'segment_std', 'month_weekend_slot_avg', 'hierarchical_fallback_avg', 'highest_revenue_weekday', 'highest_revenue_month', 'p75_price', 'p25_price', 'effective_daily_rate', 'slot_lag_price_1', 'slot_lag_price_2', 'occupancy_rate_7d', 'occupancy_rate_30d', 'booking_velocity', 'bookings_last_7d', 'bookings_last_30d', 'weekend_premium_ratio', 'summer_demand_ratio', 'winter_demand_ratio', 'rain_impact_ratio', 'segment_weighted_mean', 'month_leadtime_slot_avg', 'slot_month_weekend_diff', 'historical_variance', 'similar_booking_density_30d', 'price_momentum_30d', 'duration_from_excel', 'unnamed:_19']
drop_cols.extend(leaky_cols)
X_full = df_sorted.drop(columns=[col for col in drop_cols if col in df_sorted.columns])
cat_cols = X_full.select_dtypes(include=['object', 'category']).columns
if len(cat_cols) > 0: X_full = pd.get_dummies(X_full, columns=cat_cols, drop_first=False)
X_full.drop(columns=X_full.select_dtypes(include=['datetime', 'timedelta']).columns, inplace=True)
for c in X_full.select_dtypes(include=['bool']).columns: X_full[c] = X_full[c].astype(int)
for c in X_full.columns: X_full[c] = pd.to_numeric(X_full[c], errors="coerce").fillna(0.0).astype(float)
import re
X_full.columns = [re.sub(r'[\[\]<]', '_', str(col)) for col in X_full.columns]

# Ensure X_full matches features exactly
for f in features:
    if f not in X_full.columns:
        X_full[f] = 0
X_full = X_full[features]

# Predict
baselines = df_sorted["historical_baseline_price"].values
preds = baselines + model_B.predict(X_full)

df_sorted["predicted"] = preds
df_sorted["error"] = df_sorted["predicted"] - df_sorted["selling_price"]
df_sorted["abs_error"] = df_sorted["error"].abs()

df_sorted = df_sorted[df_sorted["selling_price"] > 0]

print("\n--- TOP 20 BIGGEST ERRORS ---")
cols_to_show = ["booking_date", "commercial_slot", "person_count", "is_weekend", "is_festival", "selling_price", "historical_baseline_price", "predicted", "error", "abs_error"]
print(df_sorted.sort_values(by="abs_error", ascending=False).head(20)[cols_to_show].to_string())

print("\n--- FESTIVAL NAME ERROR INVESTIGATION ---")
print("Are there festivals with price spikes? Let's check the festival entries.")
fests = df_sorted[df_sorted["is_festival"] == 1]
print(f"Number of festivals in dataset: {len(fests)}")
if len(fests) > 0:
    print(fests[["booking_date", "selling_price", "historical_baseline_price", "predicted", "error"]].head(10).to_string())

