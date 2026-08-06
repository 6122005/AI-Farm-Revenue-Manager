from app.services.data_pipeline import DataPipeline
from app.config import DATA_DIR
from app.services.retrieval_engine import SimilarBookingRetriever
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = DataPipeline.load_and_process_file(path)
req = {
    "start_datetime": "2026-08-06 18:00",
    "commercial_slot": "24H Night",
    "person_count": 5,
    "lead_days": 0,
    "is_weekend": 0,
    "month": 8
}
print(f"Columns: {df.columns.tolist()}")
print(f"Empty df? {df.empty}")
print(f"Rows: {len(df)}")
pool = df[(df['month'] == 8) & (df['is_weekend'] == 0)]
print(f"Pool for level 2: {len(pool)}")
ctx = SimilarBookingRetriever.retrieve(req, df)
print(f"Level: {ctx.level_used}")
if ctx.level_used == 6:
    print(df[['month', 'is_weekend', 'commercial_slot']].head())
