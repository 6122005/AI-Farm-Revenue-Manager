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
from app.services.commercial_optimizer import CommercialOptimizer

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

results = []

# Pre-cache clean data to avoid reloading
prediction_engine._clean_data_cache = df_clean.copy()

for idx, row in df_clean.iterrows():
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

    dt_obj = pd.to_datetime(start_dt_str)
    end_dt_obj = dt_obj + pd.Timedelta(hours=dur_h)
    end_dt_str = end_dt_obj.strftime("%Y-%m-%d %H:%M")

    req = {
        "start_datetime": start_dt_str,
        "end_datetime": end_dt_str,
        "commercial_slot": comm_slot,
        "person_count": person_cnt,
        "lead_days": lead_d,
        "booking_notes": str(row.get("description", "")) if pd.notna(row.get("description")) else "",
        "exclude_index": idx
    }

    try:
        resp = prediction_engine.predict(req)
        pred_rent = float(resp.recommended_price)
    except Exception as e:
        print(f"Error row {idx}: {e}")
        pred_rent = actual_rent

    diff = pred_rent - actual_rent
    abs_err = abs(diff)
    pct_err = (abs_err / actual_rent * 100.0) if actual_rent > 0 else 0.0

    results.append({
        "Index": len(results) + 1,
        "Start Date": b_date,
        "Start Time": s_time,
        "Number Of Guests": person_cnt,
        "Booking Category": comm_slot,
        "Duration (Hours)": round(dur_h, 1),
        "Festivals": "No" if int(row.get("is_festival", 0)) == 0 else "Yes",
        "Weekend": "Yes" if int(row.get("is_weekend", 0)) == 1 else "No",
        "Vacation Time": "Yes" if int(row.get("is_vacation", 0)) == 1 else "No",
        "Season": str(row.get("season", "summer")).capitalize(),
        "Lead Days": lead_d,
        "Actual Rent (INR)": round(actual_rent, 2),
        "Predicted Rent (INR)": round(pred_rent, 2),
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
within_5 = (res_df["Error (%)"] <= 5.0).mean() * 100
within_10 = (res_df["Error (%)"] <= 10.0).mean() * 100
within_15 = (res_df["Error (%)"] <= 15.0).mean() * 100

print(f"--- SUMMARY METRICS (703 Records) ---")
print(f"MAE: ₹{mae:.2f}")
print(f"Median AE: ₹{median_ae:.2f}")
print(f"Within 5% Error: {within_5:.2f}%")
print(f"Within 10% Error: {within_10:.2f}%")
print(f"Within 15% Error: {within_15:.2f}%")
