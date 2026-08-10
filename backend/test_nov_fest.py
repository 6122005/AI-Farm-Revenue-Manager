import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")
try:
    df = pd.read_excel(file_path, sheet_name="Sheet4")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    
    nov_fest = df[df["Date"].dt.month == 11]
    print(nov_fest[["Date", "Festival_Name", "Multiplier"]])
except Exception as e:
    print(e)
