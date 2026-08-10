import pandas as pd
from pathlib import Path
import json
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from app.services.prediction_engine import prediction_engine
from datetime import datetime

# 1. Load the raw data as processed by DataPipeline
path = Path("data/Farm_Booking_Data_new.xlsx")
df = DataPipeline.load_and_process_file(path)

df["month"] = pd.to_datetime(df["booking_date"], errors="coerce").dt.month
df["is_weekend"] = pd.to_datetime(df["booking_date"], errors="coerce").dt.weekday.isin([4, 5, 6]).astype(int)

jan_mask = (df["month"] == 1) & (df["is_festival"] == 0) & (df["selling_price"] >= 1500) & (df["is_weekend"] == 1)
df_jan = df[jan_mask]
print(f"Total January Weekend Non-Festival Records: {len(df_jan)}")

print("\n--- Raw Records for 24H Night ---")
jan_24h_n = df_jan[df_jan["commercial_slot"].str.upper().str.contains("24H NIGHT")]
for _, row in jan_24h_n.iterrows():
    print(f"Date: {row['booking_date']}, Duration: {row.get('duration_hours')}, Price: {row['selling_price']}, Persons: {row['person_count']}, is_weekend: {row['is_weekend']}, is_festival: {row['is_festival']}")

print("\n--- Raw Records for 24H Day ---")
jan_24h = df_jan[df_jan["commercial_slot"].str.upper().str.contains("24H DAY")]
for _, row in jan_24h.iterrows():
    print(f"Date: {row['booking_date']}, Slot: {row['commercial_slot']}, Duration: {row.get('duration_hours')}, Price: {row['selling_price']}")

# 2. Check the group averages for this specific segment
with open("data/group_averages.json", "r") as f:
    avgs = json.load(f)

print(f"\n--- Group Averages for Month 1 ---")
print("slot_month_weekend_24H Night_1_1:", avgs.get("slot_month_weekend_24H Night_1_1"))
print("seg_24H Night_1_1_mean:", avgs.get("seg_24H Night_1_1_mean"))
print("seg_24H Night_1_1_count:", avgs.get("seg_24H Night_1_1_count"))
print("global_yoy_inflation:", avgs.get("global_yoy_inflation"))

