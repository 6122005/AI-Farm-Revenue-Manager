from app.services.data_pipeline import DataPipeline
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = DataPipeline.load_and_process_file(path)
print(f"Total rows: {len(df)}")
print(f"commercial_slot NaNs: {df['commercial_slot'].isna().sum()}")
print(f"slot_type NaNs: {df['slot_type'].isna().sum()}")
print(df[['commercial_slot', 'slot_type']].head(10))
