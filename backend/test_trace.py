from app.services.prediction_engine import prediction_engine
import json

req = {
    "start_datetime": "2026-01-15 10:00",
    "commercial_slot": "24H Day",
    "person_count": 10,
    "lead_days": 10
}

res = prediction_engine.predict(req)
print(f"Final recommended price: {res['recommended_price']}")
