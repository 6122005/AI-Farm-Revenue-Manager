import pandas as pd
from pathlib import Path
from app.services.data_pipeline import DataPipeline
from app.services.prediction_engine import prediction_engine

def print_raw_rows():
    print("🚀 Extracting requested rows...")
    
    # Load raw excel to get original rates
    raw_df = DataPipeline.load_raw_dataframe(Path("data/Farm_Booking_Data_new.xlsx"))
    cols = [str(c) for c in raw_df.columns]
    price_col = next((c for c in cols if any(k in c.lower() for k in ["extracted rent", "selling_price", "rent", "price", "booked_price", "booking_amount", "amount", "rate", "cost", "tariff", "fee"])), cols[0])
    date_col = next((c for c in cols if any(k in c.lower() for k in ["start date", "booking_date", "date", "check_in", "checkin", "event_date", "day"])), cols[0])
    slot_col = next((c for c in cols if any(k in c.lower() for k in ["booking_category", "commercial_slot", "slot", "timing", "category"])), None)
    guests_col = next((c for c in cols if any(k in c.lower() for k in ["person_count", "guest", "person", "pax", "count"])), None)
    
    # Load clean df
    df_clean = prediction_engine.get_clean_data()
    
    # The requested row indices
    requested_indices = [515, 516, 252, 253, 257, 260, 265, 268]
    
    output = "| Row ID | Booking Date (Clean) | Month | Slot | Guests | Original Rate (Excel) | Selling Price (Pipeline) | ML Target (selling_price) |\n"
    output += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
    
    for idx in requested_indices:
        if idx in df_clean.index:
            clean_row = df_clean.loc[idx]
            
            b_date = clean_row.get("booking_date", "")
            month = clean_row.get("month", "")
            slot = clean_row.get("slot_type", "")
            guests = clean_row.get("person_count", "")
            selling_price = clean_row.get("selling_price", "")
            target = clean_row.get("selling_price", "")
            dur = clean_row.get("duration_hours", 12)
            
            # Find matching row in raw_df
            raw_match = None
            if b_date:
                # convert b_date to string if it is timestamp
                if isinstance(b_date, pd.Timestamp):
                    b_date_str = b_date.strftime("%Y-%m-%d")
                else:
                    b_date_str = str(b_date)[:10]
                    
                for ridx, r in raw_df.iterrows():
                    r_date = pd.to_datetime(r[date_col], errors="coerce")
                    if pd.isna(r_date):
                        continue
                    if r_date.strftime("%Y-%m-%d") == b_date_str:
                        # try to match slot (loose match since it gets normalized)
                        r_slot = str(r.get(slot_col, "")).upper().replace(" ", "_")
                        c_slot = str(slot).upper().replace(" ", "_")
                        # rough match
                        if c_slot in r_slot or r_slot in c_slot or "NIGHT" in c_slot == "NIGHT" in r_slot:
                            # match guests
                            r_guests = r.get(guests_col, "")
                            if pd.isna(r_guests) or int(r_guests) == int(guests):
                                raw_match = r
                                break
                                
            if raw_match is not None:
                orig_rate = raw_match.get(price_col, "N/A")
            else:
                orig_rate = "Match Failed"
                
            output += f"| Row #{idx} | {b_date} | {month} | {slot} | {guests} | {orig_rate} | {selling_price} | {target} |\n"
        else:
            output += f"| Row #{idx} | Not Found | - | - | - | - | - | - |\n"
            
    with open("row_analysis.md", "w") as f:
        f.write(output)
        
    print(output)

if __name__ == "__main__":
    print_raw_rows()
