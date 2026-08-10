import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")
try:
    df = pd.read_excel(file_path, sheet_name="Events Export")
    print("Unique Booking Categories in raw Excel:")
    counts = df["Booking Category"].value_counts()
    print(counts)
    
    print("\nMean Price by Category:")
    df["selling_price"] = pd.to_numeric(df["Rate"], errors="coerce")
    print(df.groupby("Booking Category")["selling_price"].mean())
    
    print("\nMedian Price by Category:")
    print(df.groupby("Booking Category")["selling_price"].median())
except Exception as e:
    print(e)
