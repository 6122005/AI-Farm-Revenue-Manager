import calendar
from datetime import datetime
from app.services.prediction_engine import prediction_engine

month_num = 2
year = 2026
slot = "24H Night"
for is_weekend in [False, True]:
    target_day = 5 if is_weekend else 1
    dt_str = None
    for day in range(1, 28):
        dt = datetime(year, month_num, day)
        if dt.weekday() == target_day:
            dt_str = dt.strftime("%Y-%m-%d 10:00")
            break
            
    req = {
        "start_datetime": dt_str,
        "commercial_slot": slot,
        "person_count": 10,
        "lead_days": 10
    }
    # is_batch=True disables optimization loop
    res = prediction_engine.predict(req, is_batch=True)
    print(f"Feb {'Weekend' if is_weekend else 'Weekday'}: base={res.get('base_price')}, final={res['recommended_price']}")
