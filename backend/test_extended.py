from app.services.prediction_engine import prediction_engine
import json

req = {
    "start_datetime": "2026-08-04 10:00",
    "commercial_slot": "77H",
    "person_count": 10,
    "lead_days": 10
}

res = prediction_engine.predict(req, is_batch=False)
print("Base:", res.get("base_price"))
print("Final:", res.get("recommended_price"))
print("Explanation:\n", res.get("explanation"))
