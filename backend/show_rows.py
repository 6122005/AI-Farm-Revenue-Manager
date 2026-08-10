import pandas as pd
from pathlib import Path
import os
import time

file_path = Path("data/Farm_Booking_Data_new.xlsx")
try:
    mtime = os.path.getmtime(file_path)
    print(f"Modification time: {time.ctime(mtime)}\n")

    df = pd.read_excel(file_path, sheet_name="Events Export")
    print(f"Total records in dataframe: {len(df)}")
    
    counts = df["Booking Category"].value_counts()
    print("\n--- Current Counts ---")
    print(counts[["24H Night", "12H Night"]] if "24H Night" in counts else counts)
    
    columns_to_show = ["Start Date", "Booking Category", "Rate"]
    columns_to_show = [c for c in columns_to_show if c in df.columns]
    
    print("\n--- Record at index 700 ---")
    if 700 < len(df):
        print(df[columns_to_show].iloc[[700]].to_string())
    else:
        print("Index 700 is out of bounds")
        
    print("\n--- Record at last index ---")
    last_idx = len(df) - 1
    print(df[columns_to_show].iloc[[last_idx]].to_string())
    
except Exception as e:
    print(e)
