import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import xgboost as xgb
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.ml_trainer import MLTrainer
import re

file_path = Path("data/Farm_Booking_Data_new.xlsx")

df_raw = DataPipeline.process_with_explicit_mapping(
    file_path, price_col="Rate", date_col="Start Date",
    slot_col="Booking Category", guests_col="Number of Guests",
    lead_col="Lead Days", competitor_col="Competitor_Price"
)
features_df = FeatureEngineer.process_dataframe(df_raw.copy())

# Emulate ml_trainer.py logic to get predictions for the ENTIRE dataset to see where the errors are
# We will use the exact data prep from MLTrainer
df_sorted = features_df.copy()
if "booking_date" in df_sorted.columns:
    df_sorted["booking_date_dt"] = pd.to_datetime(df_sorted["booking_date"], errors="coerce")
    df_sorted = df_sorted.sort_values(by="booking_date_dt").copy()
    df_sorted.drop(columns=["booking_date_dt"], inplace=True)

drop_mask = pd.Series(False, index=df_sorted.index)
if "is_festival" in df_sorted.columns:
    drop_mask = drop_mask | (df_sorted["is_festival"] == 1)
if "commercial_slot" in df_sorted.columns:
    drop_mask = drop_mask | (df_sorted["commercial_slot"] == "EXTENDED_DAY")
df_sorted = df_sorted[~drop_mask].copy()

from app.services.ml_trainer import HistoricalPricingBaseline
df_sorted = HistoricalPricingBaseline.fit_predict_expanding(df_sorted)
df_sorted["residual_target"] = df_sorted["selling_price"] - df_sorted["historical_baseline_price"]

y_rate = df_sorted["selling_price"]
y_resid = df_sorted["residual_target"]

drop_cols = ["selling_price", "residual_target", "historical_baseline_price", "baseline_level", "baseline_evidence_count", "baseline_confidence", "booking_date", "start_date", "start_datetime", "commercial_slot", "festival_name", "start_time", "end_date", "end_time", "person_count", "lead_days"]
leaky_cols = [
    'outlier_score', 'segment_mean', 'segment_trimmed_mean', 'segment_std',
    'month_weekend_slot_avg', 'hierarchical_fallback_avg', 'highest_revenue_weekday',
    'highest_revenue_month', 'p75_price', 'p25_price', 'effective_daily_rate',
    'slot_lag_price_1', 'slot_lag_price_2', 'occupancy_rate_7d', 'occupancy_rate_30d',
    'booking_velocity', 'bookings_last_7d', 'bookings_last_30d', 'weekend_premium_ratio',
    'summer_demand_ratio', 'winter_demand_ratio', 'rain_impact_ratio', 'segment_weighted_mean',
    'month_leadtime_slot_avg', 'slot_month_weekend_diff', 'historical_variance', 
    'similar_booking_density_30d', 'price_momentum_30d', 'duration_from_excel', 'unnamed:_19'
]
drop_cols.extend(leaky_cols)

X_full = df_sorted.drop(columns=[col for col in drop_cols if col in df_sorted.columns])

cat_cols = X_full.select_dtypes(include=['object', 'category']).columns
if len(cat_cols) > 0:
    X_full = pd.get_dummies(X_full, columns=cat_cols, drop_first=False)
    
dt_cols = X_full.select_dtypes(include=['datetime', 'timedelta']).columns
X_full.drop(columns=dt_cols, inplace=True)
    
for c in X_full.select_dtypes(include=['bool']).columns:
    X_full[c] = X_full[c].astype(int)
for c in X_full.columns:
    X_full[c] = pd.to_numeric(X_full[c], errors="coerce").fillna(0.0).astype(float)
    
X_full.columns = [re.sub(r'[\[\]<]', '_', str(col)) for col in X_full.columns]
features = list(X_full.columns)

# Train on 80%, predict on 20%
split_idx = int(len(X_full) * 0.8)
X_train, y_resid_train = X_full.iloc[:split_idx].copy(), y_resid.iloc[:split_idx].copy()
X_test, y_test_rate = X_full.iloc[split_idx:].copy(), y_rate.iloc[split_idx:].copy()
baseline_test = df_sorted["historical_baseline_price"].iloc[split_idx:].values

model_B = xgb.XGBRegressor(n_estimators=200, max_depth=5, learning_rate=0.05, random_state=42)
model_B.fit(X_train[features], y_resid_train)
preds_test = baseline_test + model_B.predict(X_test[features])

# Let's attach predictions back to the test set to see where the errors are
test_df = df_sorted.iloc[split_idx:].copy()
test_df['predicted_price'] = preds_test
test_df['error'] = test_df['predicted_price'] - test_df['selling_price']
test_df['abs_error'] = test_df['error'].abs()
test_df['error_pct'] = (test_df['abs_error'] / test_df['selling_price']) * 100

print("=== ERROR BY MONTH ===")
month_err = test_df.groupby('month')[['error', 'abs_error']].mean()
print(month_err)

print("\n=== ERROR BY SLOT ===")
slot_err = test_df.groupby('commercial_slot')[['error', 'abs_error']].mean()
print(slot_err)

print("\n=== ERROR BY GUEST COUNT ===")
guest_err = test_df.groupby('person_count')[['error', 'abs_error']].mean()
print(guest_err)

print("\n=== ERROR BY DURATION ===")
dur_err = test_df.groupby('duration')[['error', 'abs_error']].mean()
print(dur_err)

print("\n=== BIGGEST MISSES (Top 10) ===")
worst = test_df.sort_values(by='abs_error', ascending=False).head(10)
for idx, row in worst.iterrows():
    print(f"Date: {row.get('booking_date', 'N/A')} | Slot: {row.get('commercial_slot', 'N/A')} | Guests: {row.get('person_count', 'N/A')} | Actual: ₹{row['selling_price']:.0f} | Pred: ₹{row['predicted_price']:.0f} | Err: ₹{row['error']:.0f} ({row['error_pct']:.1f}%)")

