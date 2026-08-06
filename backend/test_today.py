from app.services.prediction_engine import prediction_engine
import traceback

today_str = "2026-08-06"
payload = {
    "booking_date": today_str,
    "start_datetime": f"{today_str} 18:00",
    "end_datetime": "2026-08-07 18:00",
    "commercial_slot": "24H Night",
    "person_count": 5,
    "lead_days": 0,
    "competitor_price": 0.0,
    "skip_consistency_check": False
}

try:
    res = prediction_engine.predict(payload)
    print("Success")
except Exception as e:
    traceback.print_exc()

