import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import r2_score
from pathlib import Path
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.historical_pricing_baseline import HistoricalPricingBaseline
import json

df_raw = DataPipeline.load_and_process_file(Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx"))
df = FeatureEngineer.process_dataframe(df_raw)

# Richer Lead Time Features
df["lead_0_1"] = ((df["lead_days"] >= 0) & (df["lead_days"] <= 1)).astype(int)
df["lead_2_7"] = ((df["lead_days"] >= 2) & (df["lead_days"] <= 7)).astype(int)
df["lead_8_14"] = ((df["lead_days"] >= 8) & (df["lead_days"] <= 14)).astype(int)
df["lead_15_30"] = ((df["lead_days"] >= 15) & (df["lead_days"] <= 30)).astype(int)
df["lead_31_plus"] = (df["lead_days"] > 30).astype(int)

df["booking_date_dt"] = pd.to_datetime(df["booking_date"], errors="coerce")
df_sorted = df.sort_values(by="booking_date_dt").copy()

# Base filters (only drop explicit manual outliers / extended days, NOT unexplained prices)
drop_mask = pd.Series(False, index=df_sorted.index)
if "commercial_slot" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["commercial_slot"] == "Extended Day")
if "is_manual_outlier" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["is_manual_outlier"] == 1)
df_sorted = df_sorted[~drop_mask].copy()

df_sorted = HistoricalPricingBaseline.fit_predict_expanding(df_sorted)
split_idx = int(len(df_sorted) * 0.8)
train_df = df_sorted.iloc[:split_idx].copy()
test_df = df_sorted.iloc[split_idx:].copy()

# Identify Unexplained High Prices instead of deleting them
def classify_demand(row, p75):
    if row["selling_price"] < p75: return "NORMAL"
    # If high price, check if explained by festival or high lead time
    if row.get("is_festival", 0) > 0 or row.get("lead_days", 0) > 30 or row.get("person_count", 0) > 10:
        return "HIGH_DEMAND_EXPLAINED"
    return "HIGH_PRICE_UNEXPLAINED"

train_df["p75_slot"] = train_df.groupby("commercial_slot")["selling_price"].transform(lambda x: x.quantile(0.75))
train_df["demand_regime"] = train_df.apply(lambda r: classify_demand(r, r["p75_slot"]), axis=1)

# Downweight unexplained high prices (0.3 weight)
train_df["sample_weight"] = np.where(train_df["demand_regime"] == "HIGH_PRICE_UNEXPLAINED", 0.3, 1.0)

# ELASTICITY ENGINE (Data-Driven)
# Calculate global elasticities for shrinkage
global_guest_elasticity = 150.0 # fallback global marginal cost per guest
global_dur_elasticity = 300.0   # fallback global marginal cost per hour

def compute_elasticity(df_group, col_name):
    # Only compute on NORMAL records to find the baseline elasticity
    sub = df_group[df_group["demand_regime"] == "NORMAL"]
    if len(sub) < 5: return 0.0, "NO_ELASTICITY", 0.0
    
    # Calculate price vs col correlation/slope
    x = sub[col_name]
    y = sub["selling_price"]
    if x.nunique() < 2: return 0.0, "NO_ELASTICITY", 0.0
    
    slope, intercept = np.polyfit(x, y, 1)
    
    # Check monotonicity
    if slope > 50:
        if len(sub) > 15: return slope, "LEARNED", slope
        else:
            # Shrink toward global
            w = len(sub) / 15.0
            shrunk = (w * slope) + ((1-w) * (global_guest_elasticity if col_name == "person_count" else global_dur_elasticity))
            return shrunk, "SHRINKED", slope
    else:
        return 0.0, "NO_ELASTICITY", slope

elasticity_map = {}
for slot, group in train_df.groupby("commercial_slot"):
    g_elas, g_mode, g_raw = compute_elasticity(group, "person_count")
    d_elas, d_mode, d_raw = compute_elasticity(group, "duration_hours")
    elasticity_map[slot] = {
        "guest": g_elas, "guest_mode": g_mode, "guest_raw": g_raw,
        "dur": d_elas, "dur_mode": d_mode, "dur_raw": d_raw
    }

# Map elasticities back
for df_obj in [train_df, test_df]:
    df_obj["guest_elasticity_factor"] = df_obj["commercial_slot"].map(lambda x: elasticity_map.get(x, {}).get("guest", 0.0))
    df_obj["dur_elasticity_factor"] = df_obj["commercial_slot"].map(lambda x: elasticity_map.get(x, {}).get("dur", 0.0))
    
    # Base price stripping for Models B, C, D
    # We strip out the elastic components so XGBoost learns the base slot price
    df_obj["stripped_price_B"] = df_obj["selling_price"] - (df_obj["person_count"] * df_obj["guest_elasticity_factor"])
    df_obj["stripped_price_C"] = df_obj["selling_price"] - (df_obj["duration_hours"] * df_obj["dur_elasticity_factor"])
    df_obj["stripped_price_D"] = df_obj["selling_price"] - (df_obj["person_count"] * df_obj["guest_elasticity_factor"]) - (df_obj["duration_hours"] * df_obj["dur_elasticity_factor"])

# Model Training Setup
drop_cols = ["selling_price", "residual_target", "historical_baseline_price", "baseline_level", "baseline_evidence_count", "baseline_confidence", "booking_date", "start_date", "start_datetime", "start_time", "end_date", "end_time", "p75_slot", "demand_regime", "sample_weight", "guest_elasticity_factor", "dur_elasticity_factor", "stripped_price_B", "stripped_price_C", "stripped_price_D"]
leaky_cols = ['segment_mean', 'segment_trimmed_mean', 'segment_std', 'month_weekend_slot_avg', 'hierarchical_fallback_avg', 'highest_revenue_weekday', 'highest_revenue_month', 'p75_price', 'p25_price', 'effective_daily_rate', 'slot_lag_price_1', 'slot_lag_price_2', 'occupancy_rate_7d', 'occupancy_rate_30d', 'booking_velocity', 'bookings_last_7d', 'bookings_last_30d', 'weekend_premium_ratio', 'summer_demand_ratio', 'winter_demand_ratio', 'rain_impact_ratio', 'segment_weighted_mean', 'month_leadtime_slot_avg', 'slot_month_weekend_diff', 'historical_variance', 'similar_booking_density_30d', 'price_momentum_30d', 'duration_from_excel', 'unnamed:_19']
drop_cols.extend(leaky_cols)

X_train = train_df.drop(columns=[col for col in drop_cols if col in train_df.columns])
cat_cols = X_train.select_dtypes(include=['object', 'category']).columns
if len(cat_cols) > 0: X_train = pd.get_dummies(X_train, columns=cat_cols, drop_first=False)
X_train.drop(columns=X_train.select_dtypes(include=['datetime', 'timedelta']).columns, inplace=True)
for c in X_train.select_dtypes(include=['bool']).columns: X_train[c] = X_train[c].astype(int)
for c in X_train.columns: X_train[c] = pd.to_numeric(X_train[c], errors="coerce").fillna(0.0).astype(float)
import re
X_train.columns = [re.sub(r'[\[\]<]', '_', str(col)) for col in X_train.columns]
features = list(X_train.columns)

X_test = test_df.drop(columns=[col for col in drop_cols if col in test_df.columns])
if len(cat_cols) > 0: X_test = pd.get_dummies(X_test, columns=cat_cols, drop_first=False)
X_test.drop(columns=X_test.select_dtypes(include=['datetime', 'timedelta']).columns, inplace=True)
for c in X_test.select_dtypes(include=['bool']).columns: X_test[c] = X_test[c].astype(int)
for c in X_test.columns: X_test[c] = pd.to_numeric(X_test[c], errors="coerce").fillna(0.0).astype(float)
X_test.columns = [re.sub(r'[\[\]<]', '_', str(col)) for col in X_test.columns]
for f in features:
    if f not in X_test.columns: X_test[f] = 0.0

# Define constraints
mono_A = {f: 1 if "person_count" in f or "duration_ratio" in f else 0 for f in features}
# Models B,C,D shouldn't strictly need XGBoost constraints for guests if the layer handles it, but we can keep it 0 or 1.
mono_B = {f: 1 if "duration_ratio" in f else 0 for f in features}
mono_C = {f: 1 if "person_count" in f else 0 for f in features}
mono_D = {f: 0 for f in features} # Layer handles both

models = {}
preds = {}

# Model A (Current)
mA = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, monotone_constraints=mono_A)
yA = train_df["selling_price"] - train_df["historical_baseline_price"]
mA.fit(X_train[features], yA)
preds["A"] = test_df["historical_baseline_price"] + mA.predict(X_test[features])

# Model B (Learned Guest)
mB = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, monotone_constraints=mono_B)
yB = train_df["stripped_price_B"] - train_df["historical_baseline_price"]
mB.fit(X_train[features], yB)
preds["B"] = test_df["historical_baseline_price"] + mB.predict(X_test[features]) + (test_df["person_count"] * test_df["guest_elasticity_factor"])

# Model C (Learned Dur)
mC = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, monotone_constraints=mono_C)
yC = train_df["stripped_price_C"] - train_df["historical_baseline_price"]
mC.fit(X_train[features], yC)
preds["C"] = test_df["historical_baseline_price"] + mC.predict(X_test[features]) + (test_df["duration_hours"] * test_df["dur_elasticity_factor"])

# Model D (Guest + Dur + Regime Weighting)
mD = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, monotone_constraints=mono_D)
yD = train_df["stripped_price_D"] - train_df["historical_baseline_price"]
mD.fit(X_train[features], yD, sample_weight=train_df["sample_weight"])
preds["D"] = test_df["historical_baseline_price"] + mD.predict(X_test[features]) + (test_df["person_count"] * test_df["guest_elasticity_factor"]) + (test_df["duration_hours"] * test_df["dur_elasticity_factor"])

# Evaluate
eval_res = {}
for name, p in preds.items():
    test_df[f"pred_{name}"] = p
    mae = np.abs(test_df["selling_price"] - p).mean()
    rmse = np.sqrt(((test_df["selling_price"] - p)**2).mean())
    r2 = r2_score(test_df["selling_price"], p)
    bias = (p - test_df["selling_price"]).mean()
    
    # Flatlining check (slope variance)
    # We'll just look at Model D vs A guest elasticity specifically
    
    eval_res[name] = {"MAE": mae, "RMSE": rmse, "R2": r2, "Bias": bias}

print("ELASTICITY MAP:")
print(json.dumps(elasticity_map, indent=2))
print("\nA/B/C/D RESULTS:")
print(json.dumps(eval_res, indent=2))

