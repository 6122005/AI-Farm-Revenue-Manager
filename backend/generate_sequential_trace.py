import pandas as pd
import numpy as np
from pathlib import Path
from app.services.data_pipeline import DataPipeline
from app.services.prediction_engine import prediction_engine
from app.services.feature_engineering import FeatureEngineer
from app.services.slot_engine import slot_engine

def run_trace():
    print("🚀 Generating Detailed Prediction Trace in sequential format...")
    
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
    
    # Calculate pure month average
    df_temp = df.copy()
    df_temp["booking_date_dt"] = pd.to_datetime(df_temp["booking_date"], errors="coerce")
    df_temp["month_idx"] = df_temp["booking_date_dt"].dt.month
    month_avg_dict = df_temp.groupby("month_idx")["selling_price"].mean().to_dict()
    
    avg_dict = FeatureEngineer.get_group_averages()
    
    md_content = "# Detailed Prediction Trace (Sequential Format)\n\n"
    
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
            lead_adj = next((getattr(f, "impact_amount", 0.0) for f in res.price_factors if getattr(f, "factor", "") == "Lead Adjustment"), 0.0)
            fest_adj = next((getattr(f, "impact_amount", 0.0) for f in res.price_factors if getattr(f, "factor", "") == "Festival Adjustment"), 0.0)
            demand_adj = next((getattr(f, "impact_amount", 0.0) for f in res.price_factors if getattr(f, "factor", "") == "Demand Adjustment"), 0.0)
            weather_adj = next((getattr(f, "impact_amount", 0.0) for f in res.price_factors if getattr(f, "factor", "") == "Weather Adjustment"), 0.0)
            ml_calib = next((getattr(f, "impact_amount", 0.0) for f in res.price_factors if getattr(f, "factor", "") == "ML Calibration"), 0.0)
            
            biz_adj = lead_adj + fest_adj + demand_adj + weather_adj + ml_calib
            
            dt = pd.to_datetime(b_date_str)
            month = dt.month
            
            is_weekend = res.is_weekend
            weekend_str = "Weekend" if is_weekend else "Weekday"
            
            hist_ids = [str(r.get("row_id", "")) for r in res.contributing_historical_rows]
            hist_prices = [str(r.get("selling_price", "")) for r in res.contributing_historical_rows]
            
            hist_ids_str = ", ".join(hist_ids) if hist_ids else "N/A"
            hist_prices_str = ", ".join(hist_prices) if hist_prices else "N/A"
            
            pure_month_avg = round(month_avg_dict.get(month, 0.0), 2)
            mo_slot_avg = avg_dict.get(f"month_slot_avg_price_{month}_{slot}", "N/A")
            mo_slot_wknd_avg = avg_dict.get(f"slot_month_weekend_{slot_norm}_{month}_{int(is_weekend)}", "N/A")
            
            if mo_slot_avg != "N/A": mo_slot_avg = round(mo_slot_avg, 2)
            if mo_slot_wknd_avg != "N/A": mo_slot_wknd_avg = round(mo_slot_wknd_avg, 2)
            
            rag_pred = round(res.rag_median_price, 2)
            ml_pred = round(res.shadow_ml_price, 2)
            final_pred = round(res.recommended_price, 2)
            
            md_content += f"### Booking BKG-{idx+1} ({b_date_str})\n\n"
            md_content += f"**Booking ID:** BKG-{idx+1}\n\n"
            md_content += "↓\n\n"
            md_content += f"**Actual Price:** {actual}\n\n"
            md_content += "↓\n\n"
            md_content += f"**Selected Historical Booking IDs:** {hist_ids_str}\n\n"
            md_content += "↓\n\n"
            md_content += f"**Selected Historical Prices:** {hist_prices_str}\n\n"
            md_content += "↓\n\n"
            md_content += f"**Historical Average:** {rag_pred}\n\n"
            md_content += "↓\n\n"
            md_content += f"**Month Average:** {pure_month_avg}\n\n"
            md_content += "↓\n\n"
            md_content += f"**Month+Slot Average:** {mo_slot_avg}\n\n"
            md_content += "↓\n\n"
            md_content += f"**Month+Slot+Weekend Average:** {mo_slot_wknd_avg}\n\n"
            md_content += "↓\n\n"
            md_content += f"**ML Prediction:** {ml_pred}\n\n"
            md_content += "↓\n\n"
            md_content += f"**Guest Adjustment:** {round(guest_adj, 2)}\n\n"
            md_content += "↓\n\n"
            md_content += f"**Business Rule Adjustment:** {round(biz_adj, 2)}\n\n"
            md_content += "↓\n\n"
            md_content += f"**Final Prediction:** {final_pred}\n\n"
            md_content += "---\n\n"
            
        except Exception as e:
            print(f"Failed BKG-{idx+1}: {e}")
            
    with open("sequential_trace_report.md", "w") as f:
        f.write(md_content)
        
    print("✅ Trace complete. Output saved to sequential_trace_report.md")

if __name__ == "__main__":
    run_trace()
