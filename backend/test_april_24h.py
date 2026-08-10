from app.services.prediction_engine import PredictionEngine
import pprint

engine = PredictionEngine()

req = {
    "start_datetime": "2026-04-04 19:00",
    "end_datetime": "2026-04-05 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}

r = engine.predict(req)
pprint.pprint(r.dict() if hasattr(r, 'dict') else vars(r))
