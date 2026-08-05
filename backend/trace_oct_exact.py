from app.services.prediction_engine import prediction_engine
import json

req = {
    "start_datetime": "2026-10-17 18:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 10
}
res = prediction_engine.predict(req)
print(f"Oct 17 Final Price: {res['final_price']}")
