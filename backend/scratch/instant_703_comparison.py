import sys
from pathlib import Path
import pandas as pd
import numpy as np

backend_dir = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend")
sys.path.insert(0, str(backend_dir))

from app.services.data_pipeline import DataPipeline
from app.services.prediction_engine import prediction_engine
from app.services.retrieval_engine import SimilarBookingRetriever
from app.services.intelligent_person_increment_engine import IntelligentPersonIncrementEngine
from app.services.historical_adjustments import HistoricalAdjustments

excel_path = backend_dir / "data" / "Farm_Booking_Data_new.xlsx"
df_clean = DataPipeline.load_and_process_file(excel_path)
print(f"Loaded {len(df_clean)} records.")

artifact = prediction_engine.model_artifact
if not artifact:
    print("No model artifact found!")
    sys.exit(1)

model = artifact["model"]
feature_cols = artifact["features"]
cat_cols = artifact.get("categorical_features", [])

# Prepare feature matrix X directly from df_clean!
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

# Batch predict raw model prices
model_type = artifact.get("model_type", "Single-Stage")
if model_type == "Hierarchical Baseline Residual":
    if "start_datetime" not in df_prep.columns:
        df_prep["start_datetime"] = pd.to_datetime(df_prep["booking_date"], errors="coerce")
    from app.services.historical_pricing_baseline import HistoricalPricingBaseline
    base_df = HistoricalPricingBaseline.fit_predict_expanding(df_prep)
    baseline_vals = base_df["historical_baseline_price"].values
    residual_vals = model["base_model"].predict(X)
    raw_preds = baseline_vals + residual_vals
else:
    if isinstance(model, dict) and "base_model" in model:
        raw_preds = model["base_model"].predict(X)
    else:
        raw_preds = model.predict(X)

raw_preds = np.maximum(500.0, raw_preds)

results = []

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

    # Fast adjustment calculation via context
    month_val = int(row.get("month", 1)) if not pd.isna(row.get("month")) else 1
    is_w_val = int(row.get("is_weekend", 0)) if not pd.isna(row.get("is_weekend")) else 0
    season_val = str(row.get("season", "summer"))

    req_dict = {
        "month": month_val,
        "is_weekend": is_w_val,
        "commercial_slot": comm_slot,
        "person_count": person_cnt,
        "lead_days": lead_d,
        "season": season_val,
        "start_datetime": start_dt_str
    }

    # Retrieve context omitting current row if needed
    df_context = df_clean.drop(index=row_idx)
    context = SimilarBookingRetriever.retrieve(req_dict, df_context)

    rep_price = float(raw_preds[idx])
    context.base_price = rep_price

    guest_adj = IntelligentPersonIncrementEngine.calculate_guest_increment(context)
    lead_adj = HistoricalAdjustments.calculate_lead_days_adjustment(context)
    demand_adj = HistoricalAdjustments.calculate_demand_adjustment(context)
    weather_adj = HistoricalAdjustments.calculate_weather_adjustment(context)

    final_price = rep_price + guest_adj["adjustment_amount"] + lead_adj["adjustment_amount"] + demand_adj["adjustment_amount"] + weather_adj["adjustment_amount"]
    final_price = round(final_price, -1)

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
        "Festivals": "No" if int(row.get("is_festival", 0)) == 0 else "Yes",
        "Weekend": "Yes" if int(row.get("is_weekend", 0)) == 1 else "No",
        "Vacation Time": "Yes" if int(row.get("is_vacation", 0)) == 1 else "No",
        "Season": season_val.capitalize(),
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
print(f"SUCCESS: Saved {len(res_df)} records to {csv_out_path}")

mae = res_df["Absolute Error (INR)"].mean()
median_ae = res_df["Absolute Error (INR)"].median()
rmse = np.sqrt((res_df["Rent Difference (INR)"] ** 2).mean())
within_5 = (res_df["Error (%)"] <= 5.0).mean() * 100
within_10 = (res_df["Error (%)"] <= 10.0).mean() * 100
within_15 = (res_df["Error (%)"] <= 15.0).mean() * 100

print(f"--- SUMMARY METRICS (703 Records) ---")
print(f"Total Evaluated Records: {len(res_df)}")
print(f"Mean Absolute Error (MAE): ₹{mae:.2f}")
print(f"Median Absolute Error: ₹{median_ae:.2f}")
print(f"Root Mean Squared Error (RMSE): ₹{rmse:.2f}")
print(f"Within 5% Margin of Error: {within_5:.2f}%")
print(f"Within 10% Margin of Error: {within_10:.2f}%")
print(f"Within 15% Margin of Error: {within_15:.2f}%")

print("\n--- SAMPLE TOP 10 PREDICTIONS ---")
print(res_df[["Index", "Start Date", "Booking Category", "Number Of Guests", "Actual Rent (INR)", "Predicted Rent (INR)", "Rent Difference (INR)", "Error (%)"]].head(10).to_string(index=False))
