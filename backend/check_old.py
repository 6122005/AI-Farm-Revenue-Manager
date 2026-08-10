import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data.xlsx")
try:
    df = pd.read_excel(file_path, sheet_name="Events Export")
    
    indices_to_check = [271, 288, 297, 338, 347, 350, 396, 411, 414, 416, 433, 439, 441, 476, 526, 530, 539, 545, 548, 569, 570, 591, 594, 605, 607, 620, 626, 632, 635, 636, 669, 723, 752]
    
    print("Old File (Farm_Booking_Data.xlsx)")
    for idx in indices_to_check:
        if 0 <= idx < len(df):
            cat = str(df.iloc[idx]['Booking Category'])
            print(f"Index {idx:<4} | {cat}")
            
except Exception as e:
    print(e)
