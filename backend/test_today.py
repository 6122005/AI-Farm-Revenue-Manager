import json
from app.services.prediction_engine import prediction_engine

today_str = "2026-08-06"
payload = {
    "booking_date": today_str,
    "start_datetime": f"{today_str} 18:00",
    "end_datetime": "2026-08-07 18:00",
    "commercial_slot": "24H Night",
    "person_count": 5,
    "lead_days": 0,
    "competitor_price": 0.0,
    "skip_consistency_check": False
}

try:
    res = prediction_engine.predict(payload)
    print(f"Final Price: {res.recommended_price}")
    print("\nFactors (Reasoning):")
    for factor in res.price_factors:
        print(f"- {factor.factor}: {factor.impact_amount}")
        
    print("\nContext:")
    print(f"RAG Base Price: {res.rag_base_price}")
    print(f"ML Model Price: {res.shadow_ml_price}")
except Exception as e:
    import traceback
    traceback.print_exc()

