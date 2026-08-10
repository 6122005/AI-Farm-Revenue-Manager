import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")
try:
    df = pd.read_excel(file_path, sheet_name="Events Export")
    
    # Filter by date around 2026-07-20 and 2026-07-25
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    
    print("--- Records on 2026-07-20 ---")
    mask1 = df["Start Date"].dt.date == pd.to_datetime("2026-07-20").date()
    print(df[mask1][["Start Date", "Booking Category", "Rate"]].to_string())
    
    print("\n--- Records on 2026-07-25 ---")
    mask2 = df["Start Date"].dt.date == pd.to_datetime("2026-07-25").date()
    print(df[mask2][["Start Date", "Booking Category", "Rate"]].to_string())

except Exception as e:
    print(e)
