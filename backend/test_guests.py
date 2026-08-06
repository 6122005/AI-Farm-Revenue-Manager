from app.services.prediction_engine import prediction_engine
req10 = {
    "start_datetime": "2026-05-16 18:00",
    "end_datetime": "2026-05-17 18:00",
    "booking_date": "2026-05-16",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 10,
    "competitor_price": 0.0,
    "skip_consistency_check": False
}
req4 = {
    "start_datetime": "2026-05-16 18:00",
    "end_datetime": "2026-05-17 18:00",
    "booking_date": "2026-05-16",
    "commercial_slot": "24H Night",
    "person_count": 4,
    "lead_days": 0,
    "competitor_price": 0.0,
    "skip_consistency_check": False
}
print(f"10 guests: {prediction_engine.predict(req10).recommended_price}")
print(f"4 guests: {prediction_engine.predict(req4).recommended_price}")
