from app.services.prediction_engine import prediction_engine
req_24 = {
    "booking_date": "2026-08-10",
    "commercial_slot": "24H Night",
    "person_count": 4,
    "duration_hours": 24,
    "lead_days": 6
}
res_24 = prediction_engine.predict(req_24, is_batch=True)
print(f"24H Night 4 Guests: {res_24.get('recommended_price')}")
