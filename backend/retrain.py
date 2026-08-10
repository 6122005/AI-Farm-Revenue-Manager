from app.services.feature_engineering import FeatureEngineer
from app.services.data_pipeline import DataPipeline
from pathlib import Path

print("Loading fresh data from Excel...")
df = DataPipeline.load_and_process_file(Path("data/Farm_Booking_Data_new.xlsx"))

print("Rebuilding group averages and features...")
features = FeatureEngineer.prepare_and_save_data(df)
print(f"Done! {len(features)} rows of features generated.")
