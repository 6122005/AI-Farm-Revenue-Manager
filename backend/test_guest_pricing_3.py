from app.services.prediction_engine import prediction_engine
import json

req = {
    "start_datetime": "2025-04-15 10:00",
    "commercial_slot": "24H Day",
    "person_count": 15,
    "lead_days": 10
}

res = prediction_engine.predict(req)
print(json.dumps(res, indent=2))
