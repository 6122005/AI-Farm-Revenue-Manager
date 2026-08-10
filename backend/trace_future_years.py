import json
from app.services.prediction_engine import PredictionEngine

engine = PredictionEngine()

req_2027 = {
    "booking_date": "2027-05-08",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "duration_hours": 24,
    "lead_days": 2,
    "start_datetime": "2027-05-08 19:00",
    "end_datetime": "2027-05-09 19:00"
}
print("--- 2027 ---")
res = engine.predict(req_2027)
print(json.dumps(res.dict(), indent=2))

print("\n--- 2028 ---")
req_2028 = {
    "booking_date": "2028-05-13",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "duration_hours": 24,
    "lead_days": 3,
    "start_datetime": "2028-05-13 19:00",
    "end_datetime": "2028-05-14 19:00"
}
res2 = engine.predict(req_2028)
print(json.dumps(res2.dict(), indent=2))
