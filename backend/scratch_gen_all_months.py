import json
import calendar
import datetime
from app.services.prediction_engine import PredictionEngine

engine = PredictionEngine()

slots = [
    "12H Day",
    "12H Night",
    "24H Day",
    "24H Night"
]

results = []

for month in range(1, 13):
    month_name = calendar.month_name[month]
    year = 2026
    
    cal = calendar.monthcalendar(year, month)
    weekday_day = next(week[1] for week in cal if week[1] != 0)
    weekend_day = next(week[5] for week in cal if week[5] != 0)
    
    wd_date = f"{year}-{month:02d}-{weekday_day:02d}"
    we_date = f"{year}-{month:02d}-{weekend_day:02d}"

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
            "lead_days": 5,
            "start_datetime": st_wd,
            "end_datetime": en_wd
        }
        try:
            res_wd = engine.predict(req_wd)
            price_wd = res_wd.recommended_price
        except Exception as e:
            print(f"Error WD {month} {s}: {e}")
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
            "lead_days": 5,
            "start_datetime": st_we,
            "end_datetime": en_we
        }
        try:
            res_we = engine.predict(req_we)
            price_we = res_we.recommended_price
        except Exception as e:
            print(f"Error WE {month} {s}: {e}")
            price_we = 0
            
        results.append({
            "Month": month_name,
            "Slot": s,
            "Weekday Price": price_wd,
            "Weekend Price": price_we
        })

markdown_table = "# All Months Price Predictions\n\n"
markdown_table += "Generated with **10 Guests** and **5 Lead Days**.\n\n"
markdown_table += "| Month | Slot | Weekday Price | Weekend Price |\n"
markdown_table += "| :--- | :--- | :--- | :--- |\n"

for r in results:
    wk_str = f"₹{r['Weekday Price']:,.0f}" if r['Weekday Price'] else "N/A"
    we_str = f"₹{r['Weekend Price']:,.0f}" if r['Weekend Price'] else "N/A"
    markdown_table += f"| {r['Month']} | {r['Slot']} | {wk_str} | {we_str} |\n"

with open("/Users/darshankanani/.gemini/antigravity-ide/brain/f85b134a-8677-463b-ab33-33093b97a4f8/all_months_prices.md", "w") as f:
    f.write(markdown_table)

print("Artifact generated successfully.")
