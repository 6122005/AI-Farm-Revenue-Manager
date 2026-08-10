import pandas as pd
from pathlib import Path
from app.services.slot_engine import slot_engine

def verify_weekend_logic():
    print("--- WEEKEND LOGIC AUDIT ---")
    file_path = Path("data/Farm_Booking_Data_new.xlsx")
    
    # 1. Find correct sheet
    xls = pd.ExcelFile(file_path)
    target_sheet = None
    for sheet_name in xls.sheet_names:
        df_preview = pd.read_excel(xls, sheet_name=sheet_name, nrows=5)
        if any("booking category" in str(c).lower() for c in df_preview.columns):
            target_sheet = sheet_name
            break
            
    raw_df = pd.read_excel(xls, sheet_name=target_sheet)
    
    # Find columns
    date_col = next((c for c in raw_df.columns if "start date" in str(c).lower()), None)
    start_t_col = next((c for c in raw_df.columns if "start time" in str(c).lower() or "checkin_time" in str(c).lower()), None)
    slot_col = next((c for c in raw_df.columns if "booking category" in str(c).lower() or "slot" in str(c).lower()), None)
    wknd_col = next((c for c in raw_df.columns if "weekend" in str(c).lower()), None)
    
    mismatches = []
    
    for idx, row in raw_df.iterrows():
        if pd.isna(row[slot_col]):
            continue
            
        raw_w = row[wknd_col]
        if pd.isna(raw_w) or str(raw_w).strip() == "":
            continue
            
        excel_val = 1 if str(raw_w).strip().upper() in ["1", "TRUE", "Y", "YES"] else 0
        
        d_str = str(row[date_col])
        t_str = str(row[start_t_col]) if start_t_col and not pd.isna(row[start_t_col]) else "00:00:00"
        
        try:
            dt_obj = pd.to_datetime(d_str)
            if dt_obj.hour == 0 and start_t_col:
                t_obj = pd.to_datetime(t_str, errors="coerce")
                if not pd.isna(t_obj):
                    dt_obj = dt_obj.replace(hour=t_obj.hour, minute=t_obj.minute)
        except:
            dt_obj = None
            
        slot = slot_engine.normalize_commercial_slot(str(row[slot_col]))
        calc_val = slot_engine.classify_weekend(dt_obj, slot)
        
        if excel_val != calc_val:
            mismatches.append({
                "Index": idx + 2, # Excel row (approx)
                "Raw Slot": row[slot_col],
                "Raw Time": row[start_t_col],
                "Day of Week": dt_obj.weekday() if dt_obj else None,
                "Slot": slot,
                "Excel": excel_val,
                "Calc": calc_val
            })
            
    print(f"Mismatch Count: {len(mismatches)}\n")
    if mismatches:
        for m in mismatches:
            print(f"Row {m['Index']}: RawSlot='{m['Raw Slot']}' RawTime='{m['Raw Time']}' Day={m['Day of Week']} | Excel={m['Excel']} Calc={m['Calc']}")
            
if __name__ == "__main__":
    verify_weekend_logic()
