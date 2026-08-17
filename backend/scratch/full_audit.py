import pandas as pd
from pathlib import Path
import json

# 1. Dataset Audit
data_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx")
df = pd.read_excel(data_path, sheet_name='Events Export')
audit = {
    "total_rows": len(df),
    "total_columns": len(df.columns),
    "column_names": df.columns.tolist(),
    "missing_values": df.isnull().sum().to_dict(),
    "unique_values": df.nunique().to_dict(),
}

# Distros
audit["guest_distribution"] = df.get("Number of Guests", pd.Series()).value_counts(dropna=False).to_dict()
audit["booking_category_distribution"] = df.get("Booking Category", pd.Series()).value_counts(dropna=False).to_dict()
audit["outlier_distribution"] = df.get("outlier ", pd.Series()).value_counts(dropna=False).to_dict()

# 2. Root Cause Analysis
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
df_proc = DataPipeline.load_and_process_file(data_path)
df_feat = FeatureEngineer.process_dataframe(df_proc)

# Root Cause 1: 12H Day + Duration < 12h
mask_12h = (df_feat["commercial_slot"] == "12H Day")
print("\n--- Root Cause 1: 12H Day with varying durations ---")
print(df_feat[mask_12h].groupby("duration_hours")["selling_price"].describe())

# Root Cause 2: Guest decreases + price increases (Inverse monotonicity)
print("\n--- Root Cause 2: Guest decreases + price increases ---")
df_12h = df_feat[mask_12h].copy()
# Group by duration, weekend, month, and see how price changes by guests
print(df_12h.groupby(["duration_hours", "is_weekend", "month", "person_count"])["selling_price"].mean().head(30))

print("\n--- AUDIT SUMMARY ---")
print(json.dumps(audit, indent=2, default=str))

