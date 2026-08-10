from app.services.prediction_engine import PredictionEngine
from app.services.manual_festival_engine import ManualFestivalEngine

# Mock the festival engine
def mock_fest(*args, **kwargs):
    return {"adjustment_amount": 0.0, "reason": "Disabled"}
ManualFestivalEngine.calculate_premium = mock_fest

engine = PredictionEngine()

req_12h = {
    "start_datetime": "2026-03-07 07:00",
    "end_datetime": "2026-03-07 19:00",
    "commercial_slot": "12H Day",
    "person_count": 10,
    "lead_days": 3
}

req_24h = {
    "start_datetime": "2026-03-07 19:00",
    "end_datetime": "2026-03-08 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3
}

r1 = engine.predict(req_12h)
r2 = engine.predict(req_24h)

print(f"12H Day without festival: {r1.recommended_price}")
print(f"24H Night without festival: {r2.recommended_price}")
