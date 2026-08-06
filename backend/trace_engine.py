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
df_raw = prediction_engine.get_historical_data()
print(f"Total raw rows: {len(df_raw)}")
df_clean = prediction_engine.extract_pure_historical_data(payload, df_raw, False)
print(f"Total clean rows for payload: {len(df_clean)}")
from app.services.retrieval_engine import SimilarBookingRetriever
ctx = SimilarBookingRetriever.retrieve(payload, df_clean)
print(f"Level used: {ctx.level_used}")
print(f"Candidates empty: {ctx.retrieved_segment.empty}")
