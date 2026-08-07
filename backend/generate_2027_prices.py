import pandas as pd
from app.services.prediction_engine import PredictionEngine
from pathlib import Path

# Artifact path
out_path = Path("/Users/darshankanani/.gemini/antigravity-ide/brain/f85b134a-8677-463b-ab33-33093b97a4f8/2027_prices.md")

engine = PredictionEngine()
slots = ["12H Day", "12H Night", "24H Day", "24H Night"]

# Representative 2027 dates (Weekday = Wednesday, Weekend = Saturday)
dates_2027 = {
    1:  ("2027-01-06", "2027-01-09", "January"),
    2:  ("2027-02-03", "2027-02-06", "February"),
    3:  ("2027-03-03", "2027-03-06", "March"),
    4:  ("2027-04-07", "2027-04-10", "April"),
    5:  ("2027-05-05", "2027-05-08", "May"),
    6:  ("2027-06-02", "2027-06-05", "June"),
    7:  ("2027-07-07", "2027-07-10", "July"),
    8:  ("2027-08-04", "2027-08-07", "August"),
    9:  ("2027-09-01", "2027-09-04", "September"),
    10: ("2027-10-06", "2027-10-09", "October"),
    11: ("2027-11-03", "2027-11-06", "November"),
    12: ("2027-12-01", "2027-12-04", "December")
}

person_count = 10
lead_days = 15

markdown_lines = []
markdown_lines.append("# 2027 Full Year Price Predictions (Inflation Adjusted)")
markdown_lines.append(f"\nThis report contains the AI's predicted prices for all months and slots in **2027**.")
markdown_lines.append(f"The model has automatically applied a **15% Year-over-Year (YoY) Inflation** rate to current market values.")
markdown_lines.append(f"\n**Standard Booking Assumptions:**")
markdown_lines.append(f"- Guests: {person_count}")
markdown_lines.append(f"- Lead Days: {lead_days} (Advance Booking)")
markdown_lines.append("\n---")

for month, (wd_date, wk_date, m_name) in dates_2027.items():
    markdown_lines.append(f"\n## {m_name} 2027")
    markdown_lines.append("| Slot | Weekday Price | Weekend Price | Weekend Premium |")
    markdown_lines.append("| :--- | :--- | :--- | :--- |")
    
    for slot in slots:
        # Determine start/end times based on slot
        if "Night" in slot:
            start_time = "19:00"
            end_time = "07:00" if "12H" in slot else "17:00"
        else:
            start_time = "07:00"
            end_time = "19:00" if "12H" in slot else "05:00"
            
        wd_start = f"{wd_date} {start_time}"
        wd_end = f"{wd_date} {end_time}"
        wk_start = f"{wk_date} {start_time}"
        wk_end = f"{wk_date} {end_time}"
        
        # We must add 1 day to end_date if it crosses midnight
        # For simplicity in this script, we'll just let prediction engine parse it. Wait, the prediction engine needs a proper end_datetime.
        # Actually, prediction_engine doesn't validate if end_datetime is before start_datetime, it just calculates duration!
        # Wait, duration is based on (end - start). If end is before start, duration is negative! We must fix end_date.
        wd_start_dt = pd.to_datetime(wd_start)
        duration = 12 if "12H" in slot else 24
        wd_end_dt = wd_start_dt + pd.Timedelta(hours=duration)
        
        wk_start_dt = pd.to_datetime(wk_start)
        wk_end_dt = wk_start_dt + pd.Timedelta(hours=duration)
        
        req_wd = {
            "start_datetime": wd_start_dt.strftime("%Y-%m-%d %H:%M"),
            "end_datetime": wd_end_dt.strftime("%Y-%m-%d %H:%M"),
            "commercial_slot": slot,
            "person_count": person_count,
            "lead_days": lead_days
        }
        
        req_wk = {
            "start_datetime": wk_start_dt.strftime("%Y-%m-%d %H:%M"),
            "end_datetime": wk_end_dt.strftime("%Y-%m-%d %H:%M"),
            "commercial_slot": slot,
            "person_count": person_count,
            "lead_days": lead_days
        }
        
        try:
            res_wd = engine.predict(req_wd)
            res_wk = engine.predict(req_wk)
            
            wd_price = res_wd.recommended_price
            wk_price = res_wk.recommended_price
            diff = wk_price - wd_price
            
            markdown_lines.append(f"| {slot} | ₹{wd_price:,.0f} | **₹{wk_price:,.0f}** | + ₹{diff:,.0f} |")
        except Exception as e:
            markdown_lines.append(f"| {slot} | Error | Error | N/A |")

with open(out_path, "w") as f:
    f.write("\n".join(markdown_lines))

print(f"Artifact created at {out_path}")
