import pandas as pd
from pathlib import Path
import os
import json

DATA_DIR = Path("app/services/data")
csv_path = DATA_DIR / "cleaned_booking_data.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
    subset = df[(df["month"] == 12) & (df["is_weekend"] == 0) & (df["slot_type"] == "24H Night")]
    print(subset[["booking_date", "person_count", "selling_price", "cmv_base_price", "year", "month"]])
    print("Median selling:", subset["selling_price"].median())
    print("Median cmv:", subset["cmv_base_price"].median())
else:
    print("CSV not found")
