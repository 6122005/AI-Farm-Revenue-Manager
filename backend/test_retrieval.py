import logging
from app.services.prediction_engine import PredictionEngine
from app.services.retrieval_engine import SimilarBookingRetriever

logging.basicConfig(level=logging.INFO)
engine = PredictionEngine()
df = engine.get_clean_data()

req_we = {
    "booking_date": "2025-06-14",
    "month": 6,
    "commercial_slot": "24H Night",
    "is_weekend": 1,
    "person_count": 4,
    "duration_hours": 24,
    "lead_days": 10
}
context = SimilarBookingRetriever.retrieve(req_we, df)
print("Context confidence:", context.confidence)
print("Context level:", context.level_used)
print("Context base price:", context.base_price)
print("Context stats:", context.stats)
print("Borrow metadata:", context.stats.get("borrowing_metadata"))
