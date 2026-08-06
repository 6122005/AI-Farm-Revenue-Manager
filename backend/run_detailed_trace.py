import pandas as pd
import numpy as np
from pathlib import Path
from app.services.data_pipeline import DataPipeline
from app.services.prediction_engine import prediction_engine
from app.services.feature_engineering import FeatureEngineer
from app.services.slot_engine import slot_engine

def run_trace():
    print("🚀 Starting Detailed Prediction Trace...")
    
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
    
    # Load averages cache
    avg_dict = FeatureEngineer.get_group_averages()
    
    results = []
    
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
            
            # Extract factors
            guest_adj = next((getattr(f, "impact_amount", 0.0) for f in res.price_factors if getattr(f, "factor", "") == "Guest Adjustment"), 0.0)
            fest_adj = next((getattr(f, "impact_amount", 0.0) for f in res.price_factors if getattr(f, "factor", "") == "Festival Adjustment"), 0.0)
            
            # Month, Weekend, Slot details
            dt = pd.to_datetime(b_date_str)
            month = dt.month
            
            # Determine weekend (including Friday night logic simplified or rely on standard dayofweek)
            # prediction_engine.predict handles this. Let's replicate simple check for lookup
            is_weekend = res.is_weekend
            
            # 4. Historical average split by Month, Slot, Weekday/Weekend
            seg_key = f"slot_month_weekend_{slot_norm}_{month}_{int(is_weekend)}"
            hist_avg_split = avg_dict.get(seg_key, "N/A")
            if hist_avg_split != "N/A":
                hist_avg_split = round(hist_avg_split, 2)
            
            # 9. Weekend Multiplier
            wknd_ratio_key = f"slot_month_weekend_ratio_{slot_norm}_{month}"
            weekend_multiplier = avg_dict.get(wknd_ratio_key, 1.0)
            
            # 10. Month Multiplier
            mo_slot = avg_dict.get(f"month_slot_avg_price_{month}_{slot}", 0.0)
            ov_slot = avg_dict.get(f"slot_overall_{slot}", 0.0)
            month_multiplier = round(mo_slot / ov_slot, 3) if ov_slot > 0 else 1.0
            
            hist_prices = [str(r.get("selling_price", "")) for r in res.contributing_historical_rows]
            hist_prices_str = ", ".join(hist_prices)
            
            results.append({
                "Booking_ID": f"BKG-{idx+1}",
                "Booking_Date": b_date_str,
                "Slot": slot,
                "Guests": guests,
                "Actual_Price": actual,
                "1_Historical_Records_Selected": res.sample_size_used,
                "2_Historical_Prices": hist_prices_str,
                "3_Historical_Avg_Before_Guest_Scaling": round(res.rag_median_price, 2),
                "4_Historical_Avg_Split(Month_Slot_Weekend)": hist_avg_split,
                "5_ML_Prediction": round(res.shadow_ml_price, 2),
                "6_RAG_Prediction": round(res.rag_median_price, 2),
                "7_Final_Blended_Price": round(res.fair_market_price, 2),
                "8_Guest_Scaling_Amount": round(guest_adj, 2),
                "9_Weekend_Multiplier": weekend_multiplier,
                "10_Month_Multiplier": month_multiplier,
                "11_Festival_Adjustment_Amount": round(fest_adj, 2),
                "12_Final_Price": round(res.recommended_price, 2)
            })
            
        except Exception as e:
            print(f"Failed BKG-{idx+1}: {e}")
            
    res_df = pd.DataFrame(results)
    res_df.to_csv("detailed_prediction_trace.csv", index=False)
    print("✅ Trace complete. Output saved to detailed_prediction_trace.csv")

if __name__ == "__main__":
    run_trace()
