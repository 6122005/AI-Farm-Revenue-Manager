import pandas as pd
from pathlib import Path
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer

data_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx")
df = DataPipeline.load_and_process_file(data_path)
df_feat = FeatureEngineer.process_dataframe(df)

if "outlier" in df_feat.columns:
    print("outlier column found!")
    print(df_feat["outlier"].value_counts(dropna=False))
else:
    print("outlier column NOT found!")

if "commercial_slot" in df_feat.columns:
    print("\nEXTENDED_DAY counts:")
    print((df_feat["commercial_slot"] == "EXTENDED_DAY").sum())

