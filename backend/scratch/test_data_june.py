import pandas as pd
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from pathlib import Path

data_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx")
df = DataPipeline.load_and_process_file(data_path)
df_feat = FeatureEngineer.process_dataframe(df)

june_data = df_feat[(df_feat["month"] == 6) & (df_feat["is_weekend"] == 1) & (df_feat["commercial_slot"] == "24H Night")].copy()
print("June Weekend 24H Night Bookings:")
for idx, row in june_data.iterrows():
    print(f"Date: {row['booking_date']} | Guests: {row['person_count']} | Price: {row['selling_price']} | Vacation: {row['is_vacation']} | Festival: {row['is_festival']}")
