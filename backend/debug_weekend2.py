from app.services.prediction_engine import PredictionEngine
import pandas as pd

engine = PredictionEngine()

req_12h = {
    "start_datetime": "2026-04-04 07:00",
    "end_datetime": "2026-04-04 19:00",
    "commercial_slot": "12H Day",
    "person_count": 10,
    "lead_days": 3
}

r1 = engine.predict(req_12h)

print("--- 12H Day ---")
print(f"Final Price: {r1.recommended_price}")
print(f"Breakdown: {r1.breakdown}")

