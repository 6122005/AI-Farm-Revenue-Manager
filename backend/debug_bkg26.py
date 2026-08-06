import pandas as pd
import numpy as np
from pathlib import Path
from app.services.data_pipeline import DataPipeline
from app.services.prediction_engine import prediction_engine
from app.services.retrieval_engine import SimilarBookingRetriever
from app.services.intelligent_person_increment_engine import IntelligentPersonIncrementEngine
from app.services.historical_adjustments import HistoricalAdjustments
from app.services.feature_engineering import FeatureEngineer
from app.services.slot_engine import slot_engine

def run_debug():
    print("🚀 Debugging BKG-26...")
    
    # Load raw excel to get original rates from the new dataset which prediction_engine uses
    file_path = Path("data/Farm_Booking_Data_new.xlsx")
    raw_df = DataPipeline.load_raw_dataframe(file_path)
    cols = [str(c) for c in raw_df.columns]
    price_col = next((c for c in cols if any(k in c.lower() for k in ["extracted rent", "selling_price", "rent", "price", "booked_price", "booking_amount", "amount", "rate", "cost", "tariff", "fee"])), cols[0])
    raw_df["Rate_Raw"] = raw_df[price_col]
    
    df = DataPipeline.load_and_process_file(file_path)
    
    # Sort and reset index to match BKG-26 logic from the trace report
    df = df.sort_values(by="booking_date").reset_index(drop=False)
    # The original index before sorting is stored in 'index'
    
    # BKG-26 is index 25
    bkg_idx = 25
    row = df.iloc[bkg_idx]
    orig_df_index = row['index']
    
    b_date_str = row["booking_date"].strftime("%Y-%m-%d") if isinstance(row["booking_date"], pd.Timestamp) else str(row["booking_date"])
    slot = row["commercial_slot"]
    guests = int(row["person_count"])
    lead = int(row.get("lead_days", 7))
    actual_price = float(row["selling_price"])
    is_weekend_bkg = int(row.get("is_weekend", 0))
    weekend_str = "Weekend" if is_weekend_bkg else "Weekday"
    month = pd.to_datetime(b_date_str).month
    
    req = {
        "start_datetime": f"{b_date_str} 10:00",
        "end_datetime": f"{b_date_str} 22:00",
        "booking_date": b_date_str,
        "commercial_slot": slot,
        "person_count": guests,
        "lead_days": lead,
        "competitor_price": 0.0,
        "skip_consistency_check": False,
        "exclude_index": orig_df_index
    }
    
    # Predict to get final values
    res = prediction_engine.predict(req)
    
    # Re-run retrieve to get context
    df_clean = prediction_engine.get_clean_data()
    if orig_df_index in df_clean.index:
        df_clean = df_clean.drop(index=orig_df_index)
        
    req_dict = {
        "start_datetime": req["start_datetime"],
        "commercial_slot": slot,
        "month": month,
        "is_weekend": is_weekend_bkg,
        "person_count": guests,
        "lead_days": lead,
    }
    context = SimilarBookingRetriever.retrieve(req_dict, df_clean)
    guest_data = IntelligentPersonIncrementEngine.calculate_guest_increment(context)
    
    # Extract records
    records_str = ""
    for i, (idx, hist_row) in enumerate(context.retrieved_segment.iterrows(), 1):
        # find original rate
        # We need to find this row in raw_df. 
        # idx is the index in df_clean, which corresponds to the original DataFrame index before sorting.
        try:
            orig_rate = raw_df.loc[idx, "Rate_Raw"]
        except:
            orig_rate = "N/A"
            
        norm_rate = hist_row['selling_price']
        dur = hist_row.get('duration_hours', 12)
        we = "Weekend" if hist_row.get('is_weekend', 0) == 1 else "Weekday"
        h_slot = hist_row.get('slot_type', '')
        
        records_str += f"Record {i}\n"
        records_str += f"Booking ID: Row #{idx}\n"
        records_str += f"Original Rate (Excel): {orig_rate}\n"
        records_str += f"Normalized Rate: {norm_rate}\n"
        records_str += f"Duration: {dur}\n"
        records_str += f"Weekend: {we}\n"
        records_str += f"Slot: {h_slot}\n\n"
        
    rag_pred = context.base_price
    
    ev = guest_data.get("evidence", {})
    slope = ev.get("slope", 0.0)
    anchor_g = ev.get("anchor_guests", 0.0)
    anchor_p = ev.get("anchor_price", 0.0)
    guest_adj = guest_data.get("adjustment_amount", 0.0)
    
    after_scaling = rag_pred + guest_adj
    ml_pred = res.shadow_ml_price
    
    ml_calib = next((getattr(f, "impact_amount", 0.0) for f in res.price_factors if getattr(f, "factor", "") == "ML Calibration"), 0.0)
    biz_adj = res.recommended_price - (rag_pred + guest_adj + ml_calib)
    
    final_pred = res.recommended_price
    abs_err = abs(final_pred - actual_price)
    
    output = f"""Booking ID : BKG-26

Requested:
Month: {month}
Weekend: {weekend_str}
Slot: {slot}
Guests: {guests}

--------------------------------

Historical Records Selected

{records_str}--------------------------------

Historical Average
Before Guest Scaling
=
{rag_pred}

--------------------------------

Guest Scaling
Slope: {slope}
Anchor Guests: {anchor_g}
Anchor Price: {anchor_p}
Adjustment: {guest_adj}

--------------------------------

Historical After Scaling
=
{after_scaling}

--------------------------------

ML Prediction
=
{ml_pred}

--------------------------------

Blend Formula
Historical Value: {rag_pred} (Base) + {guest_adj} (Guests) + {biz_adj} (Business Rules)
ML Calibration Added: {ml_calib} (bounded ±10%)
Final Prediction
=
{final_pred}

--------------------------------

Actual Price
=
{actual_price}

Absolute Error
=
{abs_err}
"""
    
    with open("bkg26_debug.txt", "w") as f:
        f.write(output)
        
    print(output)
    
if __name__ == "__main__":
    run_debug()
