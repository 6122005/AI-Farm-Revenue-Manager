from app.services.prediction_engine import PredictionEngine
import datetime

engine = PredictionEngine()
slots = ["12H Day", "12H Night", "24H Day", "24H Night"]
days = [
    ("2026-08-05 19:00", "2026-08-06 17:00", "Weekday"),
    ("2026-08-08 19:00", "2026-08-09 17:00", "Weekend")
]

print("--- NEW PREDICTIONS FOR AUGUST 2026 ---")
for slot in slots:
    for start, end, d_type in days:
        req = {
            "start_datetime": start,
            "end_datetime": end,
            "commercial_slot": slot,
            "person_count": 10,
            "lead_days": 15
        }
        res = engine.predict(req)
        print(f"{slot} {d_type}: ₹{res.recommended_price:,.0f}")
