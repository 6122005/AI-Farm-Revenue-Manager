import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")
try:
    df = pd.read_excel(file_path, sheet_name="Events Export")
    print("Unique Booking Categories in raw Excel:")
    print(df["Booking Category"].value_counts())
    
    print("\nModification time of the file:")
    import os
    import time
    mtime = os.path.getmtime(file_path)
    print(time.ctime(mtime))
except Exception as e:
    print(e)
