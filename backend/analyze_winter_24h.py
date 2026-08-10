import pandas as pd
from app.services.prediction_engine import PredictionEngine
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

engine = PredictionEngine()
months = [1, 2, 11, 12]

# Ensure cache is loaded
if engine._clean_data_cache is None:
    from app.services.data_pipeline import DataPipeline
    from pathlib import Path
    pipeline = DataPipeline()
    result = pipeline.load_and_process_file(Path("data/Farm_Booking_Data_new.xlsx"))
    engine._clean_data_cache = result[0] if isinstance(result, tuple) else result

df = engine._clean_data_cache

artifact_path = "/Users/darshankanani/.gemini/antigravity-ide/brain/f85b134a-8677-463b-ab33-33093b97a4f8/winter_24h_night_records.md"

with open(artifact_path, "w") as f:
    f.write("# Winter 24H Night Analysis (Jan, Feb, Nov, Dec)\n\n")
    f.write("This report shows the exact historical records used for the **24H Night** slot during winter months, and calculates the base median price (which represents the price for ~6 guests), and the final price predicted for 10 guests.\n\n")
    
    for month in months:
        f.write(f"## Month: {month}\n")
        for is_weekend in [0, 1]:
            day_type = "Weekend" if is_weekend == 1 else "Weekday"
            f.write(f"### {day_type}\n")
            
            # Start dates
            if is_weekend:
                if month == 11: start_date_str = "2026-11-14 19:00" # Sat
                elif month == 12: start_date_str = "2026-12-12 19:00" # Sat
                elif month == 1: start_date_str = "2026-01-10 19:00" # Sat
                elif month == 2: start_date_str = "2026-02-14 19:00" # Sat
            else:
                if month == 11: start_date_str = "2026-11-11 19:00" # Wed
                elif month == 12: start_date_str = "2026-12-09 19:00" # Wed
                elif month == 1: start_date_str = "2026-01-14 19:00" # Wed
                elif month == 2: start_date_str = "2026-02-11 19:00" # Wed
                
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M")
            end_dt = start_dt + timedelta(days=1)
            
            req = {
                "start_datetime": start_dt.strftime("%Y-%m-%d %H:%M"),
                "end_datetime": end_dt.strftime("%Y-%m-%d %H:%M"),
                "commercial_slot": "24H Night",
                "person_count": 6,
                "lead_days": 3,
                "skip_festival": True
            }
                
            pred_6 = engine.predict(req)
            req["person_count"] = 10
            pred_10 = engine.predict(req)
            
            subset = df[(df['month'] == month) & (df['is_weekend'] == is_weekend) & (df['commercial_slot'] == "24H Night")].copy()
            # Sort by date
            if len(subset) > 0:
                subset = subset.sort_values(by="booking_date", ascending=False)
            
            f.write(f"**Actual Historical Records Available:** {len(subset)}\n")
            if len(subset) > 0:
                f.write("| Date | Guests | Raw Selling Price | Base (CMV) Price |\n")
                f.write("| :--- | :---: | :--- | :--- |\n")
                for _, row in subset.iterrows():
                    cmv = row.get('cmv_base_price', 0)
                    if pd.isna(cmv): cmv = 0
                    f.write(f"| {pd.to_datetime(row['booking_date']).strftime('%Y-%m-%d')} | {row.get('person_count', '-')} | ₹{row['selling_price']} | ₹{cmv:.0f} |\n")
            
            f.write("\n")
            
            from app.services.retrieval_engine import SimilarBookingRetriever
            req_dict = req.copy()
            req_dict["month"] = pd.to_datetime(req["start_datetime"]).month
            req_dict["is_weekend"] = is_weekend
            context = SimilarBookingRetriever.retrieve(req_dict, engine._clean_data_cache)
            
            f.write(f"- **Calculated Median by AI Engine (Base Price):** ₹{context.stats.get('median', 0):.0f}\n")
            f.write(f"- **Final Predict Price (for 6 persons):** ₹{pred_6.recommended_price:.0f}\n")
            f.write(f"- **Final Predict Price (for 10 persons):** ₹{pred_10.recommended_price:.0f}\n\n")

print("Done")
