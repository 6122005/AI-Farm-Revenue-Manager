import pandas as pd
from app.services.data_pipeline import DataPipeline
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = DataPipeline.load_and_process_file(path)
print("Total 24H Night:", len(df[df["commercial_slot"] == "24H Night"]))
print("24H Night Weekend rows:", len(df[(df["commercial_slot"] == "24H Night") & (df["is_weekend"] == 1)]))
