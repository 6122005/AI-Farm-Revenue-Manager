import json
import logging
import calendar
import datetime
from app.services.prediction_engine import PredictionEngine

logging.basicConfig(level=logging.ERROR)
engine = PredictionEngine()

slots = [
    "12H Day",
    "12H Night",
    "24H Day",
    "24H Night"
]

months = list(range(1, 13))

rows = []
for m in months:
    year = 2027
    cal = calendar.monthcalendar(year, m)
    
    # Find first Tuesday for weekday
    weekday_day = next(week[1] for week in cal if week[1] != 0)
    
    # Find first Saturday for weekend
    weekend_day = next(week[5] for week in cal if week[5] != 0)
    
    wd_date = f"{year}-{m:02d}-{weekday_day:02d}"
    we_date = f"{year}-{m:02d}-{weekend_day:02d}"
    
    for s in slots:
        dur = 24 if "24H" in s else 12
        
        # Weekday
        st_wd = f"{wd_date} 19:00" if "Night" in s else f"{wd_date} 10:00"
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
            "lead_days": 10,
            "start_datetime": st_we,
            "end_datetime": en_we
        }
        try:
            res_we = engine.predict(req_we)
            price_we = res_we.recommended_price
        except Exception:
            price_we = 0
            
        month_name = calendar.month_name[m]
        rows.append(f"| {month_name} | {s} | ₹{price_wd:,.0f} | ₹{price_we:,.0f} |")

print("Matrix generated successfully.")

output_md = """# Final Monthly Prediction Matrix

This matrix contains the exact recommended prices from the AI model (after applying the NaN population fix and restoring normal fallback logic).

| Month | Slot | Normal Weekday Price | Normal Weekend Price |
| :--- | :--- | :--- | :--- |
"""

for r in rows:
    output_md += r + "\n"
    
with open("/Users/darshankanani/.gemini/antigravity-ide/brain/940e9e8a-b234-462c-a9f2-12b3a1ddd11d/final_prediction_matrix.md", "w") as f:
    f.write(output_md)
