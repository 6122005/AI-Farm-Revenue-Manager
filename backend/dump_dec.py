import pandas as pd
from pathlib import Path

df = pd.read_csv("app/services/data/cleaned_booking_data.csv")
df["month"] = pd.to_datetime(df["booking_date"]).dt.month
df_dec = df[(df["month"] == 12) & (df["is_weekend"] == 0) & (df["slot_type"] == "24H Night")]
print("Actual December Weekday 24H Night Records:")
for idx, row in df_dec.iterrows():
    print(f"{row['booking_date']} - {row['person_count']} guests - Selling Price: {row['selling_price']} - Base Selling Price: {row['base_selling_price']}")
