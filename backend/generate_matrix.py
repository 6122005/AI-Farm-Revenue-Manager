from app.services.prediction_engine import prediction_engine
from datetime import date, timedelta
import pandas as pd
import sys
import os

# Disable printing
sys.stdout = open(os.devnull, 'w')

slots = ["12H Day", "12H Night", "24H Day", "24H Night", "Couple Full Day"]
person_count = 10
lead_days = 7
months = range(1, 13)
data = []

def get_dates_for_month(m):
    wkday = None
    wkend = None
    for d in range(1, 28):
        dt = date(2026, m, d)
        if dt.weekday() == 2 and not wkday:
            wkday = dt
        if dt.weekday() == 5 and not wkend:
            wkend = dt
        if wkday and wkend:
            break
    return wkday, wkend

for slot in slots:
    duration = 24 if "24H" in slot else 12
    for m in months:
        wkday_dt, wkend_dt = get_dates_for_month(m)
        
        req_wd = {
            "booking_date": str(wkday_dt),
            "commercial_slot": slot,
            "person_count": person_count,
            "duration_hours": duration,
            "lead_days": lead_days
        }
        res_wd = prediction_engine.predict(req_wd)
        
        req_we = {
            "booking_date": str(wkend_dt),
            "commercial_slot": slot,
            "person_count": person_count,
            "duration_hours": duration,
            "lead_days": lead_days
        }
        res_we = prediction_engine.predict(req_we)
        
        data.append({
            "Slot": slot,
            "Month": m,
            "Weekday Price (₹)": res_wd.get("recommended_price", 0),
            "Weekend Price (₹)": res_we.get("recommended_price", 0)
        })

sys.stdout = sys.__stdout__
with open("final_table.md", "w") as f:
    f.write("| Slot | Month | Weekday Price (₹) | Weekend Price (₹) |\n")
    f.write("|---|---|---|---|\n")
    for row in data:
        f.write(f"| {row['Slot']} | {row['Month']} | ₹{row['Weekday Price (₹)']} | ₹{row['Weekend Price (₹)']} |\n")

print("Done!")
