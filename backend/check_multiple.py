import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")
try:
    df = pd.read_excel(file_path, sheet_name="Events Export")
    
    original_list = [273, 290, 299, 340, 349, 352, 398, 413, 416, 418, 435, 441, 443, 478, 528, 532, 541, 547, 550, 571, 572, 593, 596, 607, 609, 622, 628, 634, 637, 638, 671, 725, 754]
    
    indices_to_check = [i - 2 for i in original_list]
    
    print("Excel Row | Pandas Index | Start Date          | Booking Category | Rate")
    print("-" * 75)
    for orig, idx in zip(original_list, indices_to_check):
        if 0 <= idx < len(df):
            row = df.iloc[idx]
            date = str(row['Start Date'])
            cat = str(row['Booking Category'])
            rate = str(row['Rate'])
            print(f"{orig:<9} | {idx:<12} | {date:<19} | {cat:<16} | {rate}")
        else:
            print(f"{orig:<9} | {idx:<12} | OUT OF BOUNDS")
            
except Exception as e:
    print(e)
