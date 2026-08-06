import json
import logging
from app.services.prediction_engine import PredictionEngine
from app.services.historical_adjustments import HistoricalAdjustments
from app.services.intelligent_person_increment_engine import IntelligentPersonIncrementEngine

logging.basicConfig(level=logging.ERROR)
engine = PredictionEngine()

req = {
    "booking_date": "2027-07-19", 
    "commercial_slot": "24H Night",
    "person_count": 15,
    "duration_hours": 24,
    "lead_days": 34,
    "start_datetime": "2027-07-19 19:00",
    "end_datetime": "2027-07-20 19:00",
    "is_weekend": 0
}

df_clean = engine.get_clean_data()
from app.services.retrieval_engine import SimilarBookingRetriever
req_dict = {
    "booking_date": req["booking_date"],
    "commercial_slot": req["commercial_slot"],
    "person_count": req["person_count"],
    "lead_days": req["lead_days"],
    "is_weekend": req["is_weekend"],
    "month": 7
}
context = SimilarBookingRetriever.retrieve(req_dict, df_clean)
print("Context Base Price:", context.base_price)

guest_adj = IntelligentPersonIncrementEngine.calculate_guest_increment(context)
print("Guest Adj Amount:", guest_adj["adjustment_amount"])
print("Guest Adj Reason:", guest_adj["reason"])

lead_adj = HistoricalAdjustments.calculate_lead_days_adjustment(context)
print("Lead Adj Amount:", lead_adj["adjustment_amount"])
print("Lead Adj Reason:", lead_adj.get("reason", ""))

