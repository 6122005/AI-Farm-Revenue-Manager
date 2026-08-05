from app.services.prediction_engine import prediction_engine
import json

req = {
    "start_datetime": "2025-12-27 10:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 30
}

res = prediction_engine.predict(req)
print(json.dumps(res, indent=2))
