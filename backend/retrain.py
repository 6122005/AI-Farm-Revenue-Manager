from app.services.feature_engineering import FeatureEngineer
from app.services.data_pipeline import DataPipeline
from pathlib import Path

print("Loading fresh data from Excel...")
df = DataPipeline.load_and_process_file(Path("data/Farm_Booking_Data_new.xlsx"))

print("Done! Data processed and group averages generated.")
