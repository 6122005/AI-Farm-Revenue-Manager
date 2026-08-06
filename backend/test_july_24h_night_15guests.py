import json
import logging
from app.services.prediction_engine import PredictionEngine

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

try:
    res = engine.predict(req)
    print("Base Price (from Context):", res.fair_market_price)
    
    # We don't have access to the exact intermediate steps via the API response easily,
    # but let's print the final recommended price and the price_factors array if it exists.
    # Wait, the frontend gets price_factors! Let's check if the API returns it!
    # Ah, PredictionResponse doesn't have price_factors in the Python model, it might be added in the router.
    # Let's check what predict() returns.
    print("Recommended Price:", res.recommended_price)
    
    # Let's trace it manually by calling the specific adjustment functions
    from app.services.retrieval_engine import SimilarBookingRetriever
    df_clean = engine.get_clean_data()
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
    
    from app.services.historical_adjustments import HistoricalAdjustments
    guest_adj = HistoricalAdjustments.calculate_guest_increment(req["person_count"], context)
    print("Guest Adjustment:", guest_adj)
    
    lead_adj = HistoricalAdjustments.calculate_lead_time_premium(req["lead_days"], context)
    print("Lead Time Adjustment:", lead_adj)
    
except Exception as e:
    import traceback
    traceback.print_exc()
