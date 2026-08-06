import pandas as pd
from app.services.data_pipeline import DataPipeline
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = DataPipeline.load_and_process_file(path)
print("Unique slots:", df["commercial_slot"].unique())
print("Total 24H_DAY:", len(df[df["commercial_slot"] == "24H_DAY"]))
print("Total 24H_NIGHT:", len(df[df["commercial_slot"] == "24H_NIGHT"]))
print("24H_NIGHT Weekend rows:", len(df[(df["commercial_slot"] == "24H_NIGHT") & (df["is_weekend"] == 1)]))
