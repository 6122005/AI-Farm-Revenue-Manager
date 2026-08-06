import json
import logging
from app.services.prediction_engine import PredictionEngine

logging.basicConfig(level=logging.ERROR)
engine = PredictionEngine()

req = {
    "booking_date": "2025-06-14", # Weekend
    "commercial_slot": "24H Night",
    "person_count": 4,
    "duration_hours": 24,
    "lead_days": 10,
    "start_datetime": "2025-06-14 19:00",
    "end_datetime": "2025-06-15 19:00"
}
try:
    res = engine.predict(req)
    print("Festival name:", res.festival_name)
except Exception as e:
    import traceback
    traceback.print_exc()
