from app.services.prediction_engine import prediction_engine

# Makar Sankranti 2026 check 
req = {
    "start_datetime": "2026-01-14 07:00",
    "end_datetime": "2026-01-15 07:00",
    "commercial_slot": "24H Day",
    "person_count": 10,
    "lead_days": 10,
    "season": "Winter",
    "is_weekend": 0
}

res = prediction_engine.predict(req)
print("Base RAG Price:", res.rag_median_price)
print("Recommended Price:", res.recommended_price)

if res.demand_event_profile:
    print("DEMAND EVENT TRIGGERED:")
    print(res.demand_event_profile.model_dump())
else:
    print("NO EVENT TRIGGERED.")

