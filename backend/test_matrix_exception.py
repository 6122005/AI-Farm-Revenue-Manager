import logging
from app.services.prediction_engine import PredictionEngine

logging.basicConfig(level=logging.ERROR)
engine = PredictionEngine()

req = {
    "booking_date": "2025-01-01",
    "commercial_slot": "12H Day",
    "person_count": 4,
    "duration_hours": 12,
    "lead_days": 10,
    "start_datetime": "2025-01-01 10:00"
}
try:
    res = engine.predict(req)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
