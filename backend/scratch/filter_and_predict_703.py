import sys
from pathlib import Path
import pandas as pd
import numpy as np

backend_dir = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend")
sys.path.insert(0, str(backend_dir))

from app.services.data_pipeline import DataPipeline
from app.services.prediction_engine import prediction_engine
from app.services.historical_pricing_baseline import HistoricalPricingBaseline
from app.services.intelligent_person_increment_engine import IntelligentPersonIncrementEngine
from app.services.historical_adjustments import HistoricalAdjustments

excel_path = backend_dir / "data" / "Farm_Booking_Data_new.xlsx"
df_pipeline = DataPipeline.load_and_process_file(excel_path)

cond_not_extended = (df_pipeline['commercial_slot'] != 'Extended Day') & (df_pipeline['is_extended_booking'] == 0) & (df_pipeline['extended_stay'] == False)
cond_not_festival = (df_pipeline['is_festival'] == 0)
outlier_col_str = df_pipeline['outlier'].fillna('').astype(str).str.lower()
cond_not_outlier = (outlier_col_str != 'outlier') & (df_pipeline['is_manual_outlier'] == 0) & (df_pipeline['is_global_outlier'] == False)

df_clean = df_pipeline[cond_not_extended & cond_not_festival & cond_not_outlier].copy().reset_index(drop=True)

artifact = prediction_engine.model_artifact
model = artifact["model"]
feature_cols = artifact["features"]
cat_cols = artifact.get("categorical_features", [])

results = []

# Fit expanding baselines across clean dataset
df_base = HistoricalPricingBaseline.fit_predict_expanding(df_clean)

df_prep = df_clean.copy()
if "vacation_weekend" not in df_prep.columns and "is_vacation" in df_prep.columns and "is_weekend" in df_prep.columns:
    df_prep["vacation_weekend"] = df_prep["is_vacation"] * df_prep["is_weekend"]

for col in feature_cols:
    if col not in df_prep.columns:
        if col in cat_cols:
            df_prep[col] = "Unknown"
        else:
            df_prep[col] = 0.0

X = df_prep[feature_cols].copy()
for col in cat_cols:
    if col in X.columns:
        X[col] = X[col].astype('category')

for col in X.columns:
    if col not in cat_cols:
        X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)

base_model = model["base_model"] if isinstance(model, dict) and "base_model" in model else model
residuals = base_model.predict(X)

baselines = df_base["historical_baseline_price"].values
raw_preds = np.maximum(500.0, baselines + residuals)

for idx, (row_idx, row) in enumerate(df_clean.iterrows()):
    s_dt = row.get("start_datetime")
    if pd.isna(s_dt):
        b_date = str(row.get("booking_date", ""))
        s_time = str(row.get("start_time", "12:00:00"))
        start_dt_str = f"{b_date} {s_time[:5]}"
    elif hasattr(s_dt, "strftime"):
        start_dt_str = s_dt.strftime("%Y-%m-%d %H:%M")
        b_date = s_dt.strftime("%Y-%m-%d")
        s_time = s_dt.strftime("%H:%M")
    else:
        start_dt_str = str(s_dt)[:16]
        b_date = start_dt_str.split(" ")[0]
        s_time = start_dt_str.split(" ")[1] if " " in start_dt_str else "12:00"

    dur_h = float(row.get("duration_hours", 12.0))
    if pd.isna(dur_h) or dur_h <= 0:
        dur_h = 12.0

    comm_slot = str(row.get("commercial_slot", "12H Day"))
    person_cnt = int(row.get("person_count", 4)) if not pd.isna(row.get("person_count")) else 4
    lead_d = int(row.get("lead_days", 0)) if not pd.isna(row.get("lead_days")) else 0
    actual_rent = float(row.get("selling_price", 0.0))

    final_price = round(float(raw_preds[idx]), -1)

    diff = final_price - actual_rent
    abs_err = abs(diff)
    pct_err = (abs_err / actual_rent * 100.0) if actual_rent > 0 else 0.0

    results.append({
        "Index": idx + 1,
        "Start Date": b_date,
        "Start Time": s_time,
        "Number Of Guests": person_cnt,
        "Booking Category": comm_slot,
        "Duration (Hours)": round(dur_h, 1),
        "Festivals": "No",
        "Weekend": "Yes" if int(row.get("is_weekend", 0)) == 1 else "No",
        "Vacation Time": "Yes" if int(row.get("is_vacation", 0)) == 1 else "No",
        "Season": str(row.get("season", "summer")).capitalize(),
        "Lead Days": lead_d,
        "Actual Rent (INR)": round(actual_rent, 2),
        "Predicted Rent (INR)": round(final_price, 2),
        "Rent Difference (INR)": round(diff, 2),
        "Absolute Error (INR)": round(abs_err, 2),
        "Error (%)": round(pct_err, 2)
    })

res_df = pd.DataFrame(results)

csv_out_path = backend_dir / "data" / "comparison_703_records.csv"
res_df.to_csv(csv_out_path, index=False)

mae = res_df["Absolute Error (INR)"].mean()
median_ae = res_df["Absolute Error (INR)"].median()
rmse = np.sqrt((res_df["Rent Difference (INR)"] ** 2).mean())
within_200 = (res_df["Absolute Error (INR)"] <= 200).mean() * 100
within_300 = (res_df["Absolute Error (INR)"] <= 300).mean() * 100
within_500 = (res_df["Absolute Error (INR)"] <= 500).mean() * 100
within_5 = (res_df["Error (%)"] <= 5.0).mean() * 100

print(f"\n--- UPDATED PRODUCTION EVALUATION ({len(res_df)} Records) ---")
print(f"Total Evaluated Records: {len(res_df)}")
print(f"Mean Absolute Error (MAE): ₹{mae:.2f}")
print(f"Median Absolute Error: ₹{median_ae:.2f}")
print(f"Root Mean Squared Error (RMSE): ₹{rmse:.2f}")
print(f"Within ₹200 Error: {within_200:.2f}%")
print(f"Within ₹300 Error: {within_300:.2f}%")
print(f"Within ₹500 Error: {within_500:.2f}%")
