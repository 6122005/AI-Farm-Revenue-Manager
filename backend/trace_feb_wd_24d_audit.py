import calendar
from datetime import datetime
from app.services.prediction_engine import prediction_engine

req = {
    "start_datetime": "2026-02-04 10:00", # Wednesday (Weekday)
    "commercial_slot": "24H Day",
    "person_count": 10,
    "lead_days": 10
}
res = prediction_engine.predict(req, is_batch=False)
