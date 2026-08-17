import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import mean_absolute_error
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer

model_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/models_store/champion_model.joblib")
if not model_path.exists(): exit("No model")

artifact = joblib.load(model_path)
model = artifact["model"]["base_model"]
features = artifact["features"]

# Load Data
data_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx")
df = DataPipeline.load_and_process_file(data_path)
df_feat = FeatureEngineer.process_dataframe(df)

df_feat["booking_date_dt"] = pd.to_datetime(df_feat["booking_date"], errors="coerce")
df_sorted = df_feat.sort_values(by="booking_date_dt").copy()

# Base mask (Extended stay)
drop_mask = pd.Series(False, index=df_sorted.index)
if "commercial_slot" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["commercial_slot"] == "EXTENDED_DAY")
df_sorted = df_sorted[~drop_mask].copy()

# Add test predictions
from app.services.historical_pricing_baseline import HistoricalPricingBaseline
df_sorted = HistoricalPricingBaseline.fit_predict_expanding(df_sorted)
df_sorted["residual_target"] = df_sorted["selling_price"] - df_sorted["historical_baseline_price"]

split_idx = int(len(df_sorted) * 0.8)
test_df = df_sorted.iloc[split_idx:].copy()

drop_cols = ["selling_price", "residual_target", "historical_baseline_price", "baseline_level", "baseline_evidence_count", "baseline_confidence", "booking_date", "start_date", "start_datetime", "start_time", "end_date", "end_time"]
leaky_cols = ['segment_mean', 'segment_trimmed_mean', 'segment_std', 'month_weekend_slot_avg', 'hierarchical_fallback_avg', 'highest_revenue_weekday', 'highest_revenue_month', 'p75_price', 'p25_price', 'effective_daily_rate', 'slot_lag_price_1', 'slot_lag_price_2', 'occupancy_rate_7d', 'occupancy_rate_30d', 'booking_velocity', 'bookings_last_7d', 'bookings_last_30d', 'weekend_premium_ratio', 'summer_demand_ratio', 'winter_demand_ratio', 'rain_impact_ratio', 'segment_weighted_mean', 'month_leadtime_slot_avg', 'slot_month_weekend_diff', 'historical_variance', 'similar_booking_density_30d', 'price_momentum_30d', 'duration_from_excel', 'unnamed:_19']
drop_cols.extend(leaky_cols)

X_test = test_df.drop(columns=[c for c in drop_cols if c in test_df.columns])
cat_cols = X_test.select_dtypes(include=['object', 'category']).columns
if len(cat_cols) > 0: X_test = pd.get_dummies(X_test, columns=cat_cols, drop_first=False)
X_test.drop(columns=X_test.select_dtypes(include=['datetime', 'timedelta']).columns, inplace=True)
for c in X_test.select_dtypes(include=['bool']).columns: X_test[c] = X_test[c].astype(int)
for c in X_test.columns: X_test[c] = pd.to_numeric(X_test[c], errors="coerce").fillna(0.0).astype(float)
import re
X_test.columns = [re.sub(r'[\[\]<]', '_', str(col)) for col in X_test.columns]

# Ensure features match
for f in features:
    if f not in X_test.columns: X_test[f] = 0.0

test_df["prediction"] = test_df["historical_baseline_price"] + model.predict(X_test[features])

print("=== MAE BY CATEGORY ===")
groups = test_df.groupby("commercial_slot")
for name, group in groups:
    if len(group) > 5:
        mae = mean_absolute_error(group["selling_price"], group["prediction"])
        avg_price = group["selling_price"].mean()
        print(f"Slot: {name:15} | Avg True Price: ₹{avg_price:<6.0f} | MAE: ₹{mae:.0f} ({(mae/avg_price)*100:.1f}%)")

print("\n=== MAE BY PRICE TIER ===")
bins = [0, 3000, 7000, 20000]
labels = ["Budget (< ₹3k)", "Standard (₹3k - ₹7k)", "Premium (> ₹7k)"]
test_df["tier"] = pd.cut(test_df["selling_price"], bins=bins, labels=labels)
for name, group in test_df.groupby("tier"):
    if len(group) > 0:
        mae = mean_absolute_error(group["selling_price"], group["prediction"])
        avg_price = group["selling_price"].mean()
        print(f"Tier: {name:20} | Avg Price: ₹{avg_price:<6.0f} | MAE: ₹{mae:.0f} ({(mae/avg_price)*100:.1f}%)")
