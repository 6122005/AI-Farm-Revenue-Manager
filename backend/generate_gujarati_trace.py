import pandas as pd
import numpy as np
from pathlib import Path
from app.services.data_pipeline import DataPipeline
from app.services.prediction_engine import prediction_engine
from app.services.feature_engineering import FeatureEngineer
from app.services.slot_engine import slot_engine

def run_trace():
    print("🚀 Generating Detailed Prediction Trace in requested format...")
    
    df = DataPipeline.process_with_explicit_mapping(
        file_path=Path("data/Farm_Booking_Data.xlsx"),
        date_col="booking_date",
        slot_col="commercial_slot",
        price_col="selling_price",
        guests_col="person_count",
        lead_col="lead_days",
        competitor_col="competitor_price"
    )
    df = df.sort_values(by="booking_date").reset_index(drop=True)
    
    avg_dict = FeatureEngineer.get_group_averages()
    
    md_content = "# Detailed Prediction Trace\n\n"
    
    for idx, row in df.iterrows():
        b_date_str = row["booking_date"].strftime("%Y-%m-%d") if isinstance(row["booking_date"], pd.Timestamp) else str(row["booking_date"])
        slot = row["commercial_slot"]
        slot_norm = slot_engine.normalize_commercial_slot(slot)
        guests = int(row["person_count"])
        lead = int(row.get("lead_days", 7))
        actual = float(row["selling_price"])
        
        req = {
            "start_datetime": f"{b_date_str} 10:00",
            "end_datetime": f"{b_date_str} 22:00",
            "booking_date": b_date_str,
            "commercial_slot": slot,
            "person_count": guests,
            "lead_days": lead,
            "competitor_price": 0.0,
            "skip_consistency_check": False
        }
        
        try:
            res = prediction_engine.predict(req)
            
            guest_adj = next((getattr(f, "impact_amount", 0.0) for f in res.price_factors if getattr(f, "factor", "") == "Guest Adjustment"), 0.0)
            
            dt = pd.to_datetime(b_date_str)
            month = dt.month
            
            is_weekend = res.is_weekend
            weekend_str = "Weekend" if is_weekend else "Weekday"
            
            # Historical IDs & Prices
            hist_ids = [str(r.get("row_id", "")) for r in res.contributing_historical_rows]
            hist_prices = [str(r.get("selling_price", "")) for r in res.contributing_historical_rows]
            
            hist_ids_str = ", ".join(hist_ids) if hist_ids else "N/A"
            hist_prices_str = ", ".join(hist_prices) if hist_prices else "N/A"
            
            # Historical Averages
            wd_avg = avg_dict.get(f"slot_month_weekend_{slot_norm}_{month}_0", "N/A")
            we_avg = avg_dict.get(f"slot_month_weekend_{slot_norm}_{month}_1", "N/A")
            mo_avg = avg_dict.get(f"month_slot_avg_price_{month}_{slot}", "N/A")
            
            if wd_avg != "N/A": wd_avg = round(wd_avg, 2)
            if we_avg != "N/A": we_avg = round(we_avg, 2)
            if mo_avg != "N/A": mo_avg = round(mo_avg, 2)
            
            before_scaling = round(res.rag_median_price, 2)
            after_scaling = round(res.rag_median_price + guest_adj, 2)
            
            ml_pred = round(res.shadow_ml_price, 2)
            blended_pred = round(res.fair_market_price, 2)
            
            md_content += f"### Booking BKG-{idx+1} ({b_date_str})\n\n"
            md_content += "| Step | Attribute | Value |\n"
            md_content += "| ---- | --------- | ----- |\n"
            md_content += f"| 1 | Requested Month | {month} |\n"
            md_content += f"| 2 | Requested Slot | {slot} |\n"
            md_content += f"| 3 | Requested Weekday/Weekend | {weekend_str} |\n"
            md_content += f"| 4 | Selected Historical Booking IDs | {hist_ids_str} |\n"
            md_content += f"| 5 | દરેક Historical Record નું Actual Price | {hist_prices_str} |\n"
            md_content += f"| 6 | Historical Average Before Scaling | {before_scaling} |\n"
            md_content += f"| 7 | Weekday Historical Average | {wd_avg} |\n"
            md_content += f"| 8 | Weekend Historical Average | {we_avg} |\n"
            md_content += f"| 9 | Month Historical Average | {mo_avg} |\n"
            md_content += f"| 10 | Guest Scaling પહેલાં અને પછીનો Price | Before: {before_scaling}, After: {after_scaling} |\n"
            md_content += f"| 11 | ML Prediction | {ml_pred} |\n"
            md_content += f"| 12 | Final Blended Prediction | {blended_pred} |\n\n"
            
        except Exception as e:
            print(f"Failed BKG-{idx+1}: {e}")
            
    with open("gujarati_trace_report.md", "w") as f:
        f.write(md_content)
        
    print("✅ Trace complete. Output saved to gujarati_trace_report.md")

if __name__ == "__main__":
    run_trace()
