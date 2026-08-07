import pandas as pd
from app.services.prediction_engine import PredictionEngine
from pathlib import Path

# Artifact path
out_path = Path("/Users/darshankanani/.gemini/antigravity-ide/brain/f85b134a-8677-463b-ab33-33093b97a4f8/2026_prices.md")

engine = PredictionEngine()
slots = ["12H Day", "12H Night", "24H Day", "24H Night"]

# Representative 2026 dates (Weekday = Wednesday, Weekend = Saturday)
dates_2026 = {
    1:  ("2026-01-07", "2026-01-10", "January"),
    2:  ("2026-02-04", "2026-02-07", "February"),
    3:  ("2026-03-04", "2026-03-07", "March"),
    4:  ("2026-04-01", "2026-04-04", "April"),
    5:  ("2026-05-06", "2026-05-09", "May"),
    6:  ("2026-06-03", "2026-06-06", "June"),
    7:  ("2026-07-01", "2026-07-04", "July"),
    8:  ("2026-08-05", "2026-08-08", "August"),
    9:  ("2026-09-02", "2026-09-05", "September"),
    10: ("2026-10-07", "2026-10-10", "October"),
    11: ("2026-11-04", "2026-11-07", "November"),
    12: ("2026-12-02", "2026-12-05", "December")
}

# Configuration for the full year baseline
person_count = 10
lead_days = 3

markdown_lines = []
markdown_lines.append("# 2026 Full Year Price Predictions (Hybrid Inflation, No Festivals)")
markdown_lines.append("")
markdown_lines.append(f"The model has automatically applied a **10% YoY Inflation** for Mar-Oct, and **0% YoY Inflation** for Nov-Feb.")
markdown_lines.append("")
markdown_lines.append(f"**Standard Booking Assumptions:**")
markdown_lines.append(f"- Guests: {person_count}")
markdown_lines.append(f"- Lead Days: {lead_days} (Short Notice Booking)")
markdown_lines.append(f"- Note: Festival/Holiday overrides have been **disabled** for this baseline report.")
markdown_lines.append("\n---")

for month, (wd_date, wk_date, m_name) in dates_2026.items():
    markdown_lines.append(f"\n## {m_name} 2026")
    markdown_lines.append("| Slot | Weekday Price | Weekend Price | Weekend Premium |")
    markdown_lines.append("| :--- | :--- | :--- | :--- |")
    
    for slot in slots:
        if "Night" in slot:
            start_time = "19:00"
            end_time = "07:00" if "12H" in slot else "17:00"
        else:
            start_time = "07:00"
            end_time = "19:00" if "12H" in slot else "05:00"
            
        wd_start = f"{wd_date} {start_time}"
        wk_start = f"{wk_date} {start_time}"
        
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
            "lead_days": lead_days,
            "skip_festival": True
        }
        
        req_wk = {
            "start_datetime": wk_start_dt.strftime("%Y-%m-%d %H:%M"),
            "end_datetime": wk_end_dt.strftime("%Y-%m-%d %H:%M"),
            "commercial_slot": slot,
            "person_count": person_count,
            "lead_days": lead_days,
            "skip_festival": True
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
