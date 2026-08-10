import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")
try:
    df = pd.read_excel(file_path, sheet_name="Events Export")
    columns_to_show = ["Start Date", "Booking Category", "Rate"]
    columns_to_show = [c for c in columns_to_show if c in df.columns]
    print(df[columns_to_show].iloc[[754]].to_string())
except Exception as e:
    print(e)
