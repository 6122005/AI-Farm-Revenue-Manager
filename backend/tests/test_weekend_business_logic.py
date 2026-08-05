import pandas as pd
from pathlib import Path
import os
import sys

sys.path.append(str(Path(__file__).parent.parent))
from datetime import datetime

def compute_business_weekend(start_dt: datetime, slot_type: str) -> int:
    day_of_week = start_dt.weekday()
    hour = start_dt.hour
    # Saturday >= 17:00 only for night slots
    if day_of_week == 5 and "Night" in slot_type and hour >= 17:
        return 1
    # Sunday 06:00-12:00 only for day slots
    if day_of_week == 6 and "Day" in slot_type and 6 <= hour <= 12:
        return 1
    return 0

def run_validation():
    file_path = Path(__file__).parent.parent / "data" / "Farm_Booking_Data_new.xlsx"
    print(f"Validating business logic against: {file_path.name}")
    
    df = pd.read_excel(file_path, sheet_name='Events Export')
    df.columns = df.columns.str.strip()
    
    mismatches = 0
    tested = 0
    
    for idx, row in df.iterrows():
        if pd.isna(row.get('Start Date')) or pd.isna(row.get('Booking Category')):
            continue
            
        start_dt = pd.to_datetime(row['Start Date'])
        slot = str(row['Booking Category']).strip()
        
        raw_weekend = str(row.get('Weekend', '')).strip().upper()
        excel_weekend = 1 if raw_weekend in ['1', 'TRUE', 'Y', 'YES'] else 0
        
        python_weekend = compute_business_weekend(start_dt, slot)
        
        tested += 1
        if excel_weekend != python_weekend:
            print(f"[MISMATCH] Row {idx+2}: Date={start_dt.strftime('%Y-%m-%d %H:%M')} ({start_dt.day_name()}), Slot={slot}. Excel={excel_weekend}, Python={python_weekend}")
            mismatches += 1
            
    print(f"\nTested {tested} rows.")
    if mismatches > 0:
        print(f"FAILED: Found {mismatches} mismatches.")
        sys.exit(1)
    else:
        print("PASSED: 100% Match with official business definition!")
        sys.exit(0)

if __name__ == "__main__":
    run_validation()
