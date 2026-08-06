from app.database import SessionLocal
from app.models.db_models import BookingRecord
db = SessionLocal()
records = db.query(BookingRecord).filter(BookingRecord.canonical_event_id.isnot(None)).all()
print(f"Total rows with canonical_event_id: {len(records)}")
for r in records[:5]:
    print(r.canonical_event_id)
