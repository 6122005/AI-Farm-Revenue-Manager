import logging
import calendar
import datetime
from app.services.prediction_engine import PredictionEngine

logging.basicConfig(level=logging.ERROR)
engine = PredictionEngine()

months_to_check = [8, 9]  # August and September
slots = ["24H Night"] # Focus on 24H Night for clarity

print(f"{'Month':<12} | {'Slot':<12} | {'Weekday Price':<15} | {'Weekend Price':<15}")
print("-" * 60)

for m in months_to_check:
    year = 2027 # 2027 is used in generate_matrix_fixed.py
    cal = calendar.monthcalendar(year, m)
    
    # Find first Tuesday for weekday
    weekday_day = next(week[1] for week in cal if week[1] != 0)
    
    # Find first Saturday for weekend
    weekend_day = next(week[5] for week in cal if week[5] != 0)
    
    wd_date = f"{year}-{m:02d}-{weekday_day:02d}"
    we_date = f"{year}-{m:02d}-{weekend_day:02d}"
    
    for s in slots:
        dur = 24
        
        # Weekday
        st_wd = f"{wd_date} 19:00"
        end_dt_wd = datetime.datetime.strptime(st_wd, "%Y-%m-%d %H:%M") + datetime.timedelta(hours=dur)
        en_wd = end_dt_wd.strftime("%Y-%m-%d %H:%M")
        
        req_wd = {
            "booking_date": wd_date,
            "commercial_slot": s,
            "person_count": 10,
            "duration_hours": dur,
            "lead_days": 10,
            "start_datetime": st_wd,
            "end_datetime": en_wd
        }
        try:
            res_wd = engine.predict(req_wd)
            price_wd = res_wd.recommended_price
        except Exception as e:
            price_wd = 0
            print(f"Error wd: {e}")
            
        # Weekend
        st_we = f"{we_date} 19:00"
        end_dt_we = datetime.datetime.strptime(st_we, "%Y-%m-%d %H:%M") + datetime.timedelta(hours=dur)
        en_we = end_dt_we.strftime("%Y-%m-%d %H:%M")
        
        req_we = {
            "booking_date": we_date,
            "commercial_slot": s,
            "person_count": 10,
            "duration_hours": dur,
            "lead_days": 10,
            "start_datetime": st_we,
            "end_datetime": en_we
        }
        try:
            res_we = engine.predict(req_we)
            price_we = res_we.recommended_price
        except Exception as e:
            price_we = 0
            print(f"Error we: {e}")
            
        month_name = calendar.month_name[m]
        print(f"{month_name:<12} | {s:<12} | ₹{price_wd:<14,.0f} | ₹{price_we:<14,.0f}")
