from app.services.prediction_engine import prediction_engine

# Diwali 2026 check (assume Diwali is somewhere in Nov 2026)
req = {
    "start_datetime": "2026-11-09 19:00",
    "end_datetime": "2026-11-10 18:00",
    "commercial_slot": "24H Night",
    "person_count": 15,
    "lead_days": 30,
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

