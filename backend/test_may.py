from app.services.prediction_engine import prediction_engine
import traceback

req = {
    "start_datetime": "2026-05-16 18:00",
    "end_datetime": "2026-05-17 18:00",
    "booking_date": "2026-05-16",
    "commercial_slot": "24H Night",
    "person_count": 4,
    "lead_days": 0,
    "competitor_price": 0.0,
    "skip_consistency_check": False
}

try:
    res = prediction_engine.predict(req)
    print(f"Final Price: {res.recommended_price}")
    for factor in res.price_factors:
        print(f"- {factor.factor}: {factor.impact_amount}")
except Exception as e:
    traceback.print_exc()
