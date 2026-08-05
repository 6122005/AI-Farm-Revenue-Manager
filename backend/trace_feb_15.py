from app.services.prediction_engine import prediction_engine
import json

req = {
    "start_datetime": "2026-02-15 10:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 10
}
res = prediction_engine.predict(req)
print(f"Feb 15 (Sunday) Final Price: {res['final_price']}")

req2 = {
    "start_datetime": "2026-02-14 18:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 10
}
res2 = prediction_engine.predict(req2)
print(f"Feb 14 (Saturday) Final Price: {res2['final_price']}")

