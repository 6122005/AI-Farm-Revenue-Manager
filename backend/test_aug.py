from app.services.prediction_engine import PredictionEngine
import datetime

engine = PredictionEngine()
slots = ["12H Day", "12H Night", "24H Day", "24H Night"]
days = [
    (datetime.date(2026, 8, 5), "Weekday"),
    (datetime.date(2026, 8, 8), "Weekend")
]

print("--- NEW PREDICTIONS FOR AUGUST 2026 ---")
for slot in slots:
    for d, d_type in days:
        req = {
            "booking_date": d,
            "commercial_slot": slot,
            "person_count": 10,
            "lead_days": 15
        }
        res = engine.predict(req)
        print(f"{slot} {d_type}: ₹{res.get('final_predicted_price', 0):,.0f}")
