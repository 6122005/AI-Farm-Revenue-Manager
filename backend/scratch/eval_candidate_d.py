import joblib
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

df["booking_date_dt"] = pd.to_datetime(df["booking_date"], errors="coerce")
df_sorted = df.sort_values(by="booking_date_dt").copy()

# Base exclusions (Must be identical)
drop_mask = pd.Series(False, index=df_sorted.index)
if "commercial_slot" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["commercial_slot"] == "Extended Day")
if "is_manual_outlier" in df_sorted.columns: drop_mask = drop_mask | (df_sorted["is_manual_outlier"] == 1)
df_sorted = df_sorted[~drop_mask].copy()

# Add Rich Lead Time Features (Available to both if they want, but Model D uses them)
df_sorted["lead_0_1"] = ((df_sorted["lead_days"] >= 0) & (df_sorted["lead_days"] <= 1)).astype(int)
df_sorted["lead_2_7"] = ((df_sorted["lead_days"] >= 2) & (df_sorted["lead_days"] <= 7)).astype(int)
df_sorted["lead_8_14"] = ((df_sorted["lead_days"] >= 8) & (df_sorted["lead_days"] <= 14)).astype(int)
df_sorted["lead_15_30"] = ((df_sorted["lead_days"] >= 15) & (df_sorted["lead_days"] <= 30)).astype(int)
df_sorted["lead_31_plus"] = (df_sorted["lead_days"] > 30).astype(int)

df_sorted = HistoricalPricingBaseline.fit_predict_expanding(df_sorted)
df_sorted["residual_target"] = df_sorted["selling_price"] - df_sorted["historical_baseline_price"]

# Calculate Z-Scores for anomaly detection
mean_res = df_sorted["residual_target"].mean()
std_res = df_sorted["residual_target"].std()
df_sorted["z_score"] = np.abs((df_sorted["residual_target"] - mean_res) / std_res)

# Split index exactly at 80% of valid records
split_idx = int(len(df_sorted) * 0.8)
train_full = df_sorted.iloc[:split_idx].copy()
test_full = df_sorted.iloc[split_idx:].copy()

# --- MODEL A (Champion) TRAINING PREP ---
# Model A deletes noise
smart_noise_mask = (train_full["z_score"] > 2.0) & (train_full.get("is_vacation", 0) == 0) & (train_full.get("is_festival", 0) == 0)
train_A = train_full[~smart_noise_mask].copy()

# --- MODEL D (Candidate) TRAINING PREP ---
# Model D keeps noise, but applies data-driven statistical regime weighting
def classify_demand(row, p75):
    if row["selling_price"] < p75: return "NORMAL"
    if row.get("is_festival", 0) > 0 or row.get("lead_days", 0) > 30 or row.get("person_count", 0) > 10:
        return "HIGH_DEMAND_EXPLAINED"
    return "HIGH_PRICE_UNEXPLAINED"

train_full["p75_slot"] = train_full.groupby("commercial_slot")["selling_price"].transform(lambda x: x.quantile(0.75))
train_full["demand_regime"] = train_full.apply(lambda r: classify_demand(r, r["p75_slot"]), axis=1)

# Statistical Data-Driven Weighting: weight = 1.0 / (1.0 + max(0, z_score - 1.0))
# If z_score <= 1.0, weight is 1.0. If z_score is huge, weight shrinks asymptotically.
train_full["statistical_weight"] = np.where(
    train_full["demand_regime"] == "HIGH_PRICE_UNEXPLAINED",
    1.0 / (1.0 + np.maximum(0, train_full["z_score"] - 1.0)),
    1.0
)
train_D = train_full.copy()

# ELASTICITY ENGINE (Data-Driven)
global_guest_elasticity = 150.0 
global_dur_elasticity = 300.0   

def compute_elasticity(df_group, col_name):
    sub = df_group[df_group["demand_regime"] == "NORMAL"]
    if len(sub) < 5: return 0.0, "NO_ELASTICITY"
    x = sub[col_name]
    y = sub["selling_price"]
    if x.nunique() < 2: return 0.0, "NO_ELASTICITY"
    slope, intercept = np.polyfit(x, y, 1)
    
    if slope > 50:
        if len(sub) > 15: return slope, "LEARNED"
        else:
            w = len(sub) / 15.0
            shrunk = (w * slope) + ((1-w) * (global_guest_elasticity if col_name == "person_count" else global_dur_elasticity))
            return shrunk, "SHRINKED"
    else:
        return 0.0, "NO_ELASTICITY"

elasticity_map = {}
for slot, group in train_D.groupby("commercial_slot"):
    g_elas, g_mode = compute_elasticity(group, "person_count")
    d_elas, d_mode = compute_elasticity(group, "duration_hours")
    elasticity_map[slot] = {"guest": g_elas, "guest_mode": g_mode, "dur": d_elas, "dur_mode": d_mode}

for df_obj in [train_D, test_full]:
    df_obj["guest_elasticity_factor"] = df_obj["commercial_slot"].map(lambda x: elasticity_map.get(x, {}).get("guest", 0.0))
    df_obj["dur_elasticity_factor"] = df_obj["commercial_slot"].map(lambda x: elasticity_map.get(x, {}).get("dur", 0.0))
    df_obj["stripped_price_D"] = df_obj["selling_price"] - (df_obj["person_count"] * df_obj["guest_elasticity_factor"]) - (df_obj["duration_hours"] * df_obj["dur_elasticity_factor"])

# Clean features for models
def get_X(df_in):
    drop_cols = ["selling_price", "residual_target", "historical_baseline_price", "baseline_level", "baseline_evidence_count", "baseline_confidence", "booking_date", "start_date", "start_datetime", "start_time", "end_date", "end_time", "p75_slot", "demand_regime", "statistical_weight", "guest_elasticity_factor", "dur_elasticity_factor", "stripped_price_D", "z_score"]
    leaky_cols = ['segment_mean', 'segment_trimmed_mean', 'segment_std', 'month_weekend_slot_avg', 'hierarchical_fallback_avg', 'highest_revenue_weekday', 'highest_revenue_month', 'p75_price', 'p25_price', 'effective_daily_rate', 'slot_lag_price_1', 'slot_lag_price_2', 'occupancy_rate_7d', 'occupancy_rate_30d', 'booking_velocity', 'bookings_last_7d', 'bookings_last_30d', 'weekend_premium_ratio', 'summer_demand_ratio', 'winter_demand_ratio', 'rain_impact_ratio', 'segment_weighted_mean', 'month_leadtime_slot_avg', 'slot_month_weekend_diff', 'historical_variance', 'similar_booking_density_30d', 'price_momentum_30d', 'duration_from_excel', 'unnamed:_19']
    drop_cols.extend(leaky_cols)
    X = df_in.drop(columns=[c for c in drop_cols if c in df_in.columns])
    cat_cols = X.select_dtypes(include=['object', 'category']).columns
    if len(cat_cols) > 0: X = pd.get_dummies(X, columns=cat_cols, drop_first=False)
    X.drop(columns=X.select_dtypes(include=['datetime', 'timedelta']).columns, inplace=True)
    for c in X.select_dtypes(include=['bool']).columns: X[c] = X[c].astype(int)
    for c in X.columns: X[c] = pd.to_numeric(X[c], errors="coerce").fillna(0.0).astype(float)
    import re
    X.columns = [re.sub(r'[\[\]<]', '_', str(col)) for col in X.columns]
    return X

X_train_A = get_X(train_A)
X_train_D = get_X(train_D)
X_test = get_X(test_full)

# Ensure all have same columns
all_cols = list(set(X_train_A.columns) | set(X_train_D.columns) | set(X_test.columns))
for f in all_cols:
    if f not in X_train_A.columns: X_train_A[f] = 0.0
    if f not in X_train_D.columns: X_train_D[f] = 0.0
    if f not in X_test.columns: X_test[f] = 0.0
# Sort columns identically
X_train_A = X_train_A[all_cols]
X_train_D = X_train_D[all_cols]
X_test = X_test[all_cols]

# Train A
mono_A = {f: 1 if "person_count" in f or "duration_ratio" in f else 0 for f in all_cols}
mA = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42, monotone_constraints=mono_A)
mA.fit(X_train_A, train_A["residual_target"])
pred_A = test_full["historical_baseline_price"] + mA.predict(X_test)

# Train D
mD = xgb.XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, random_state=42)
mD.fit(X_train_D, train_D["stripped_price_D"] - train_D["historical_baseline_price"], sample_weight=train_D["statistical_weight"])
pred_D = test_full["historical_baseline_price"] + mD.predict(X_test) + (test_full["person_count"] * test_full["guest_elasticity_factor"]) + (test_full["duration_hours"] * test_full["dur_elasticity_factor"])

# Evaluate
test_full["pred_A"] = pred_A
test_full["pred_D"] = pred_D

res = {}
for m in ["A", "D"]:
    mae = np.abs(test_full["selling_price"] - test_full[f"pred_{m}"]).mean()
    rmse = np.sqrt(((test_full["selling_price"] - test_full[f"pred_{m}"])**2).mean())
    r2 = r2_score(test_full["selling_price"], test_full[f"pred_{m}"])
    bias = (test_full[f"pred_{m}"] - test_full["selling_price"]).mean()
    
    # Revenue capture (Sum of Pred / Sum of Actual)
    rev_cap = test_full[f"pred_{m}"].sum() / test_full["selling_price"].sum()
    
    # High price underprediction
    p75 = test_full["selling_price"].quantile(0.75)
    high_mask = test_full["selling_price"] >= p75
    hp_bias = (test_full.loc[high_mask, f"pred_{m}"] - test_full.loc[high_mask, "selling_price"]).mean()
    hp_cap = test_full.loc[high_mask, f"pred_{m}"].sum() / test_full.loc[high_mask, "selling_price"].sum()
    
    res[m] = {
        "MAE": mae, "RMSE": rmse, "R2": r2, "Bias": bias, 
        "Rev_Capture": rev_cap, "HP_Bias": hp_bias, "HP_Capture": hp_cap
    }

print("ELASTICITY MODES:")
print(json.dumps(elasticity_map, indent=2))
print("\nAPPLES-TO-APPLES EVAL:")
print(json.dumps(res, indent=2))
