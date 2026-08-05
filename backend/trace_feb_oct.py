from app.services.prediction_engine import prediction_engine
import json

print("=== February 24H Night Weekend ===")
req_feb = {
    "start_datetime": "2026-02-14 18:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 10
}
res_feb = prediction_engine.predict(req_feb)
print(json.dumps(res_feb, indent=2))

print("\n=== October 24H Night Weekend ===")
req_oct = {
    "start_datetime": "2026-10-17 18:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 10
}
res_oct = prediction_engine.predict(req_oct)
print(json.dumps(res_oct, indent=2))
