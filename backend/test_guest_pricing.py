from app.services.prediction_engine import prediction_engine
import json

req = {
    "start_datetime": "2025-03-13 10:00",
    "commercial_slot": "24H Night",
    "person_count": 20,
    "lead_days": 30
}

res = prediction_engine.predict(req)
print(json.dumps(res, indent=2))
