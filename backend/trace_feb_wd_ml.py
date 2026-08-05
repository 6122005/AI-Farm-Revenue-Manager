import calendar
from datetime import datetime
from app.services.prediction_engine import prediction_engine

req = {
    "start_datetime": "2026-02-05 10:00", # Thursday (Weekday)
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 10
}
res = prediction_engine.predict(req, is_batch=True)
print(f"Base price: {res.get('base_price')}, Final price: {res['recommended_price']}")
