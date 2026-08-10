import json
from app.services.prediction_engine import PredictionEngine

engine = PredictionEngine()
req = {
    "booking_date": "2026-11-14",  # A Saturday in Nov 2026
    "commercial_slot": "24H Night",
    "person_count": 10,
    "duration_hours": 24,
    "lead_days": 3,
    "start_datetime": "2026-11-14 19:00",
    "end_datetime": "2026-11-15 19:00",
    "skip_festival": True
}

print("Tracing November 24H Night Weekend...")
res = engine.predict(req)
print(json.dumps(res.dict(), indent=2))
