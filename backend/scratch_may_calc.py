import pandas as pd
from app.services.prediction_engine import PredictionEngine

def trace_prediction():
    engine = PredictionEngine()
    req = {
        "start_datetime": "2026-05-16 19:00", # Saturday
        "end_datetime": "2026-05-17 19:00",
        "commercial_slot": "24H Night",
        "person_count": 10,
        "lead_days": 3
    }
    
    print("--- TRACING MAY 24H NIGHT WEEKEND PREDICTION ---")
    res = engine.predict(req)
    print(f"Final Optimized Price: {res.revenue_optimized_price}")
    print(f"Fair Market Price: {res.fair_market_price}")
    print("Breakdown Factors:")
    for f in res.price_factors:
        print(f"  {f.factor}: {f.impact_amount} ({f.description})")

if __name__ == "__main__":
    trace_prediction()
