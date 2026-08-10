from app.services.prediction_engine import PredictionEngine
import json

engine = PredictionEngine()

# November Weekday from generate_2026_prices.py
req_gen = {
    "start_datetime": "2026-11-04 19:00",
    "end_datetime": "2026-11-05 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}
res_gen = engine.predict(req_gen)
print("generate_2026_prices.py (Nov 4):", res_gen.recommended_price)
print(json.dumps(res_gen.model_dump(), indent=2))
print("-" * 50)

# November Weekday from analyze_all_months_24h.py
req_ana = {
    "start_datetime": "2026-11-11 19:00",
    "end_datetime": "2026-11-12 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}
res_ana = engine.predict(req_ana)
print("analyze_all_months_24h.py (Nov 11):", res_ana.recommended_price)
print(json.dumps(res_ana.model_dump(), indent=2))
