from app.services.prediction_engine import prediction_engine
req = {
    "start_datetime": "2026-08-06 18:00",
    "end_datetime": "2026-08-07 18:00",
    "commercial_slot": "24H Night",
    "person_count": 5,
    "lead_days": 0
}
res = prediction_engine.predict(req)
print(res.debug_audit)
