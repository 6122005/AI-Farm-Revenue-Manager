from app.services.prediction_engine import prediction_engine

req = {
    "start_datetime": "2026-02-07 10:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 10
}
res = prediction_engine.predict(req)
print(f"Feb 7 (Saturday) Final Price: {res['final_price']}")
