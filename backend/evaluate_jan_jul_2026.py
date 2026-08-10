import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from sklearn.metrics import mean_absolute_error, r2_score
from app.services.prediction_engine import PredictionEngine
from app.services.data_pipeline import DataPipeline

print("--- Starting 2026 Jan-Jul Evaluation ---")
engine = PredictionEngine()

# 1. Load the raw mapped data directly to get actual records
df_all = DataPipeline.load_and_process_file(Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx"))

# 2. Filter for Year 2026, Months 1-7
df_2026 = df_all[(df_all['year'] == 2026) & (df_all['month'] >= 1) & (df_all['month'] <= 7)].copy()

print(f"Total 2026 Jan-Jul records found: {len(df_2026)}")

results = []
actuals = []
preds = []

# Loop through each record and predict
for idx, row in df_2026.iterrows():
    try:
        # Construct the exact prediction request
        # We need start_datetime and end_datetime. The dataframe has 'booking_date' and duration_hours.
        # Let's try to reconstruct them.
        booking_date = row.get("booking_date")
        slot_type = row.get("commercial_slot", "12H Day")
        person_count = int(row.get("person_count", 4))
        lead_days = int(row.get("lead_days", 7))
        actual_price = float(row.get("selling_price", 0))
        
        # Approximate start/end time based on slot
        start_date_str = str(booking_date)[:10]
        if "Night" in slot_type:
            start_time = "19:00"
            end_time = "07:00" if "12H" in slot_type else "17:00"
        else:
            start_time = "07:00"
            end_time = "19:00" if "12H" in slot_type else "05:00"
            
        start_dt_str = f"{start_date_str} {start_time}"
        
        # Calculate end datetime
        start_dt_obj = datetime.strptime(start_dt_str, "%Y-%m-%d %H:%M")
        duration = float(row.get("duration_hours", 12))
        end_dt_obj = start_dt_obj + pd.Timedelta(hours=duration)
        end_dt_str = end_dt_obj.strftime("%Y-%m-%d %H:%M")
        
        req = {
            "start_datetime": start_dt_str,
            "end_datetime": end_dt_str,
            "commercial_slot": slot_type,
            "person_count": person_count,
            "lead_days": lead_days,
            "exclude_index": idx  # VERY IMPORTANT to avoid data leakage
        }
        
        res = engine.predict(req)
        predicted_price = res.recommended_price
        
        results.append({
            "date": start_date_str,
            "slot": slot_type,
            "weekend": "Weekend" if row.get("is_weekend") == 1 else "Weekday",
            "guests": person_count,
            "lead": lead_days,
            "actual": actual_price,
            "predicted": predicted_price,
            "error": predicted_price - actual_price,
            "abs_error": abs(predicted_price - actual_price)
        })
        actuals.append(actual_price)
        preds.append(predicted_price)
        
    except Exception as e:
        print(f"Error processing index {idx}: {e}")

if len(actuals) > 0:
    mae = mean_absolute_error(actuals, preds)
    r2 = r2_score(actuals, preds)
    
    # Calculate MAPE safely
    actuals_np = np.array(actuals)
    preds_np = np.array(preds)
    mape = np.mean(np.abs((actuals_np - preds_np) / actuals_np)) * 100
    
    print("\n=== EVALUATION RESULTS (2026 Jan-Jul) ===")
    print(f"Total Evaluated Records : {len(actuals)}")
    print(f"Mean Absolute Error (MAE): ₹{mae:.2f}")
    print(f"MAPE (Percentage Error): {mape:.2f}%")
    print(f"R-squared (Accuracy)   : {r2*100:.2f}%")
    
    # Save detailed results to CSV for inspection
    res_df = pd.DataFrame(results)
    res_df.to_csv("evaluation_jan_jul_2026.csv", index=False)
    print("\nDetailed results saved to 'evaluation_jan_jul_2026.csv'")
    
    # Let's print the top 5 worst predictions
    worst = res_df.sort_values("abs_error", ascending=False).head(10)
    print("\n--- Top 10 Worst Predictions ---")
    print(worst[["date", "slot", "weekend", "guests", "actual", "predicted", "error"]].to_string())
    
    # Let's print the top 5 best predictions
    best = res_df.sort_values("abs_error", ascending=True).head(5)
    print("\n--- Top 5 Best Predictions ---")
    print(best[["date", "slot", "weekend", "guests", "actual", "predicted", "error"]].to_string())
else:
    print("No valid records found for evaluation.")

