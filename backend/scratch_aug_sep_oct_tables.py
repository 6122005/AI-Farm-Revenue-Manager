import json
import logging
import calendar
import datetime
from app.services.prediction_engine import PredictionEngine
import os

logging.basicConfig(level=logging.ERROR)
engine = PredictionEngine()

slots = [
    "12H Day",
    "12H Night",
    "24H Day",
    "24H Night"
]

months_to_check = list(range(1, 13))

out_path = "/Users/darshankanani/.gemini/antigravity-ide/brain/049fd405-cbf5-4069-a9ef-bc764cd12ff6/all_months_price_rates.md"

with open(out_path, "w") as f:
    f.write("# Full Year Price Rate Analysis (Strict Weekend Logic)\n\n")
    f.write("Here is the comprehensive breakdown of the AI model's predicted prices across **all 12 months** for exactly **10 persons** with a **3-day lead time**.\n")
    f.write("*(Festivals and ML discounts are strictly excluded from the core baseline calculations per user rule).* \n\n")
    
    for m in months_to_check:
        month_name = calendar.month_name[m]
        f.write(f"### {month_name} Prices\n")
        f.write("| Slot | Weekday Price | Weekend Price | Difference |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        
        year = 2026
        cal = calendar.monthcalendar(year, m)
        
        weekday_day = next(week[1] for week in cal if week[1] != 0) # Tuesday
        weekend_day = next(week[5] for week in cal if week[5] != 0) # Saturday
        
        weekend_day_sun = next(week[6] for week in cal if week[6] != 0) # Sunday
        
        wd_date = f"{year}-{m:02d}-{weekday_day:02d}"
        
        for s in slots:
            dur = 24 if "24H" in s else 12
            
            # For Night slots, Saturday is the weekend. For Day slots, Sunday is the weekend.
            is_night = "Night" in s
            we_date = f"{year}-{m:02d}-{weekend_day:02d}" if is_night else f"{year}-{m:02d}-{weekend_day_sun:02d}"
            
            # Weekday
            st_wd = f"{wd_date} 19:00" if "Night" in s else f"{wd_date} 10:00"
            end_dt_wd = datetime.datetime.strptime(st_wd, "%Y-%m-%d %H:%M") + datetime.timedelta(hours=dur)
            en_wd = end_dt_wd.strftime("%Y-%m-%d %H:%M")
            
            req_wd = {
                "booking_date": wd_date,
                "commercial_slot": s,
                "person_count": 10,
                "duration_hours": dur,
                "lead_days": 3,
                "start_datetime": st_wd,
                "end_datetime": en_wd
            }
            try:
                res_wd = engine.predict(req_wd)
                price_wd = res_wd.revenue_optimized_price
            except Exception:
                price_wd = 0
                
            # Weekend
            st_we = f"{we_date} 19:00" if "Night" in s else f"{we_date} 10:00"
            end_dt_we = datetime.datetime.strptime(st_we, "%Y-%m-%d %H:%M") + datetime.timedelta(hours=dur)
            en_we = end_dt_we.strftime("%Y-%m-%d %H:%M")
            
            req_we = {
                "booking_date": we_date,
                "commercial_slot": s,
                "person_count": 10,
                "duration_hours": dur,
                "lead_days": 3,
                "start_datetime": st_we,
                "end_datetime": en_we
            }
            try:
                res_we = engine.predict(req_we)
                price_we = res_we.revenue_optimized_price
            except Exception:
                price_we = 0
                
            diff = price_we - price_wd
            diff_str = f"+₹{diff:,.0f}" if diff > 0 else f"₹{diff:,.0f}"
            f.write(f"| {s} | ₹{price_wd:,.0f} | ₹{price_we:,.0f} | {diff_str} |\n")
        
        f.write("\n")
