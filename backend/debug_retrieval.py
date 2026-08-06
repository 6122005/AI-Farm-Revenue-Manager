from app.services.retrieval_engine import SimilarBookingRetriever
import pandas as pd
from app.database import SessionLocal
from app.models.db_models import BookingRecord
db = SessionLocal()
records = db.query(BookingRecord).all()
data = [r.__dict__ for r in records]
df = pd.DataFrame(data)
df["commercial_slot"] = df["slot_type"]
req = {
    "start_datetime": "2026-08-06 18:00",
    "commercial_slot": "24H Night",
    "person_count": 5,
    "lead_days": 0,
    "is_weekend": 0,
    "month": 8
}
ctx = SimilarBookingRetriever.retrieve(req, df)
print(f"Level used: {ctx.level_used}")
print(f"Candidates empty: {ctx.retrieved_segment.empty}")
if ctx.borrowing_metadata:
    print(f"Borrowing metadata: {ctx.borrowing_metadata}")
