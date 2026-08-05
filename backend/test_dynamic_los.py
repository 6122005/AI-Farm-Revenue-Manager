from app.services.prediction_engine import prediction_engine
import json

req_normal = {
    "start_datetime": "2026-08-04 10:00",
    "commercial_slot": "77H",
    "person_count": 10,
    "lead_days": 10
}

req_last_minute = {
    "start_datetime": "2026-08-04 10:00",
    "commercial_slot": "77H",
    "person_count": 10,
    "lead_days": 1
}

res1 = prediction_engine.predict(req_normal, is_batch=False)
print("--- Normal Booking (77H) ---")
print(res1.get("explanation"))

res2 = prediction_engine.predict(req_last_minute, is_batch=False)
print("\n--- Last Minute Booking (77H, Lead=1) ---")
print(res2.get("explanation"))
