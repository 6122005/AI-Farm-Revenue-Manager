from app.services.prediction_engine import PredictionEngine
import pprint

engine = PredictionEngine()

# Scenario 1: April 12H Day Weekend (High Weekend Price)
req1 = {
    "start_datetime": "2026-04-04 07:00",
    "end_datetime": "2026-04-04 19:00",
    "commercial_slot": "12H Day",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}

# Scenario 2: Nov 24H Night Weekday (High Weekday Price)
req2 = {
    "start_datetime": "2026-11-04 19:00",
    "end_datetime": "2026-11-05 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}

print("\n--- April 12H Day Weekend ---")
try:
    r1 = engine.predict(req1)
    pprint.pprint(r1.dict() if hasattr(r1, 'dict') else vars(r1))
except Exception as e:
    print(f"Error: {e}")

print("\n--- November 24H Night Weekday ---")
try:
    r2 = engine.predict(req2)
    pprint.pprint(r2.dict() if hasattr(r2, 'dict') else vars(r2))
except Exception as e:
    print(f"Error: {e}")

