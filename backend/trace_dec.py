from app.services.prediction_engine import PredictionEngine
import pprint

engine = PredictionEngine()
req = {
    "start_datetime": "2026-12-02 19:00",
    "end_datetime": "2026-12-03 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}
r = engine.predict(req)
d = r.dict() if hasattr(r, 'dict') else vars(r)
pprint.pprint(d['price_factors'])
print("Final Price:", d['recommended_price'])
print("Base Median:", d['rag_median_price'])
