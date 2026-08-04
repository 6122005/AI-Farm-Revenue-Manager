from app.services.prediction_engine import prediction_engine
req_10 = {
    "booking_date": "2026-08-10",
    "commercial_slot": "12H Day",
    "person_count": 10,
    "duration_hours": 12,
    "lead_days": 6
}
res_10 = prediction_engine.predict(req_10)
print(f"12H Day 10 Guests: {res_10.get('recommended_price')}")
