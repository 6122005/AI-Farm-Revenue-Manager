import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")
try:
    df = pd.read_excel(file_path, sheet_name="Events Export")
    
    print(f"--- Full Record at index 100 ---")
    if 100 < len(df):
        pd.set_option('display.max_columns', None)
        print(df.iloc[[100]].to_string())
    else:
        print("Index 100 is out of bounds")
        
except Exception as e:
    print(e)
