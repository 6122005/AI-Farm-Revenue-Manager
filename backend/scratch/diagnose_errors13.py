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
drop_mask = pd.Series(False, index=df_sorted.index)
if "is_festival" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["is_festival"] == 1)
if "commercial_slot" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["commercial_slot"] == "EXTENDED_DAY")
if "is_global_outlier" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["is_global_outlier"] == True)

df_clean = df_sorted[~drop_mask].copy()

df_clean = HistoricalPricingBaseline.fit_predict_expanding(df_clean)
df_clean["residual_target"] = df_clean["selling_price"] - df_clean["historical_baseline_price"]

mean_res = df_clean["residual_target"].mean()
std_res = df_clean["residual_target"].std()
z_scores = np.abs((df_clean["residual_target"] - mean_res) / std_res)
df_super_clean = df_clean[z_scores < 1.5].copy() 

y_rate = df_super_clean["selling_price"]
y_resid = df_super_clean["residual_target"]

drop_cols = ["selling_price", "residual_target", "historical_baseline_price", "baseline_level", "baseline_evidence_count", "baseline_confidence", "booking_date", "start_date", "start_datetime", "commercial_slot", "festival_name", "start_time", "end_date", "end_time"]
leaky_cols = ['outlier_score', 'segment_mean', 'segment_trimmed_mean', 'segment_std', 'month_weekend_slot_avg', 'hierarchical_fallback_avg', 'highest_revenue_weekday', 'highest_revenue_month', 'p75_price', 'p25_price', 'effective_daily_rate', 'slot_lag_price_1', 'slot_lag_price_2', 'occupancy_rate_7d', 'occupancy_rate_30d', 'booking_velocity', 'bookings_last_7d', 'bookings_last_30d', 'weekend_premium_ratio', 'summer_demand_ratio', 'winter_demand_ratio', 'rain_impact_ratio', 'segment_weighted_mean', 'month_leadtime_slot_avg', 'slot_month_weekend_diff', 'historical_variance', 'similar_booking_density_30d', 'price_momentum_30d', 'duration_from_excel', 'unnamed:_19']
drop_cols.extend(leaky_cols)
X_full = df_super_clean.drop(columns=[col for col in drop_cols if col in df_super_clean.columns])
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

model_B = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
model_B.fit(X_train[features], y_resid_train)

test_baselines = df_super_clean["historical_baseline_price"].iloc[split_idx:].values
preds_B = test_baselines + model_B.predict(X_test[features])

print(f"R² (Z < 1.5, n_estimators=100): {r2_score(y_test, preds_B):.4f}")
