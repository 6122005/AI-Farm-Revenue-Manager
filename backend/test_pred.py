from app.services.prediction_engine import prediction_engine
res = prediction_engine.predict({"booking_date": "2026-05-02", "commercial_slot": "24H Night", "person_count": 10, "duration_hours": 24, "lead_days": 7})
print(res)
