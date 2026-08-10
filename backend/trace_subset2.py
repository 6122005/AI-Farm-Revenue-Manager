from app.services.prediction_engine import PredictionEngine
engine = PredictionEngine()
req = {
    "start_datetime": "2026-12-02 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}
context = engine._get_pricing_context(req, "24H Night", 10)
print(context.subset[["booking_date", "person_count", "selling_price", "cmv_base_price"]])
