from app.database import SessionLocal
from app.models.db_models import BookingRecord
db = SessionLocal()
print("Total rows:", db.query(BookingRecord).count())
