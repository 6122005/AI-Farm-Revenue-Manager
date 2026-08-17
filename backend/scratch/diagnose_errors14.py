import pandas as pd
import numpy as np
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
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

df_sorted = df_sorted[~drop_mask].copy()

# WE MUST NOT DROP OUTLIERS, WE WANT TO LEARN THEM!
# Let's modify the baseline hierarchy inline just for a test!
def test_baseline(df_in):
    df_out = df_in.copy()
    
    h_months = df_out["month"]
    h_cats = df_out["commercial_slot"]
    h_weekends = df_out["is_weekend"]
    h_guests = df_out["guest_band"] = pd.cut(df_out["person_count"], bins=[0, 4, 10, 20, 100], labels=["1-4", "5-10", "11-20", "20+"], right=True).astype(str)
    h_vac = df_out["is_vacation"]
    
    preds = []
    
    # We don't expand, we just use the whole historical dataset for baseline (like the actual test)
    for idx, row in df_out.iterrows():
        c_m, c_c, c_w, c_g, c_v = row["month"], row["commercial_slot"], row["is_weekend"], row["guest_band"], row["is_vacation"]
        
        # Level 1: Month x Category x Weekend x Guest x Vacation
        m1 = (h_months == c_m) & (h_cats == c_c) & (h_weekends == c_w) & (h_guests == c_g) & (h_vac == c_v)
        if m1.sum() >= 3:
            preds.append(df_out[m1]["selling_price"].median())
            continue
            
        # Level 2: Month x Category x Weekend x Vacation (Ignore guests)
        m2 = (h_months == c_m) & (h_cats == c_c) & (h_weekends == c_w) & (h_vac == c_v)
        if m2.sum() >= 3:
            preds.append(df_out[m2]["selling_price"].median())
            continue
            
        # Level 3: Category x Weekend x Vacation (Ignore month)
        m3 = (h_cats == c_c) & (h_weekends == c_w) & (h_vac == c_v)
        if m3.sum() >= 3:
            preds.append(df_out[m3]["selling_price"].median())
            continue
            
        # Fallback
        preds.append(df_out[h_cats == c_c]["selling_price"].median())
        
    df_out["historical_baseline_price"] = preds
    return df_out

df_sorted = test_baseline(df_sorted)
df_sorted["residual_target"] = df_sorted["selling_price"] - df_sorted["historical_baseline_price"]

y_rate = df_sorted["selling_price"]
y_resid = df_sorted["residual_target"]

drop_cols = ["selling_price", "residual_target", "historical_baseline_price", "baseline_level", "baseline_evidence_count", "baseline_confidence", "booking_date", "start_date", "start_datetime", "commercial_slot", "festival_name", "start_time", "end_date", "end_time"]
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
features = list(X_full.columns)

split_idx = int(len(X_full) * 0.8)
X_train, y_train = X_full.iloc[:split_idx].copy(), y_rate.iloc[:split_idx].copy()
y_resid_train = y_resid.iloc[:split_idx].copy()
X_test, y_test = X_full.iloc[split_idx:].copy(), y_rate.iloc[split_idx:].copy()

model_B = XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
model_B.fit(X_train[features], y_resid_train)

test_baselines = df_sorted["historical_baseline_price"].iloc[split_idx:].values
preds_B = test_baselines + model_B.predict(X_test[features])

print(f"R² (Baseline with is_vacation, NO outlier removal): {r2_score(y_test, preds_B):.4f}")
