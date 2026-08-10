from app.services.prediction_engine import PredictionEngine
import pprint

engine = PredictionEngine()

req_feb_12h_wd = {
    "start_datetime": "2026-02-07 07:00",
    "end_datetime": "2026-02-07 19:00",
    "commercial_slot": "12H Day",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}

req_mar_12h_wd = {
    "start_datetime": "2026-03-07 07:00",
    "end_datetime": "2026-03-07 19:00",
    "commercial_slot": "12H Day",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}

req_nov_24h_wk = {
    "start_datetime": "2026-11-07 19:00",
    "end_datetime": "2026-11-08 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}

req_dec_24h_wd = {
    "start_datetime": "2026-12-02 19:00",
    "end_datetime": "2026-12-03 19:00",
    "commercial_slot": "24H Night",
    "person_count": 10,
    "lead_days": 3,
    "skip_festival": True
}

def print_trace(name, req):
    print(f"\n{'='*50}\n{name}\n{'='*50}")
    try:
        r = engine.predict(req)
        # Manually extract just the useful parts for the explanation
        d = r.dict() if hasattr(r, 'dict') else vars(r)
        print(f"Final Price: {d.get('recommended_price')}")
        print(f"Base Historical Median: {d.get('rag_median_price')}")
        print("Historical Bookings Used:")
        for b in d.get('contributing_historical_rows', []):
            print(f"  - Date: {b['booking_date']}, Slot: {b['commercial_slot']}, Guests: {b['person_count']}, Price: {b['selling_price']}")
        print(f"Fallback Info: {d.get('fallback_explainability', {})}")
        
    except Exception as e:
        print(f"Error: {e}")

print_trace("FEB 12H DAY WEEKEND", req_feb_12h_wd)
print_trace("MAR 12H DAY WEEKEND", req_mar_12h_wd)
print_trace("NOV 24H NIGHT WEEKEND", req_nov_24h_wk)
print_trace("DEC 24H NIGHT WEEKDAY", req_dec_24h_wd)

