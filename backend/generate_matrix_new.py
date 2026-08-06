from app.services.prediction_engine import prediction_engine
import pandas as pd
import calendar
from datetime import datetime

year = 2026
slots = ["12H Day", "12H Night", "24H Day", "24H Night"]

# Helper to find a specific weekday/weekend in a month
def get_sample_date(month, is_weekend, slot):
    # Weekday: Tuesday (1), Weekend: Saturday (5)
    target_day = 5 if is_weekend else 1
    hour = "18:00" if "Night" in slot else "10:00"
    for day in range(1, 28):
        dt = datetime(year, month, day)
        if dt.weekday() == target_day:
            return dt.strftime(f"%Y-%m-%d {hour}")
    return None

results = []

for month in range(1, 13):
    month_name = calendar.month_name[month]
    for slot in slots:
        for is_weekend in [0, 1]:
            dt_str = get_sample_date(month, is_weekend, slot)
            dt_obj = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            dur = 24 if "24H" in slot else 12
            end_dt = dt_obj + pd.Timedelta(hours=dur)
            req = {
                "start_datetime": dt_str,
                "end_datetime": end_dt.strftime("%Y-%m-%d %H:%M"),
                "booking_date": dt_obj.strftime("%Y-%m-%d"),
                "commercial_slot": slot,
                "person_count": 4,
                "lead_days": 0,
                "competitor_price": 0.0,
                "skip_consistency_check": False
            }
            try:
                res = prediction_engine.predict(req)
                price = res.recommended_price
            except Exception as e:
                price = 0
                print(f"Error on {month_name} {slot}: {e}")
                import traceback
                traceback.print_exc()
                
            day_type = "Weekend" if is_weekend else "Weekday"
            results.append({
                "Month": month_name,
                "Slot Type": slot,
                "Day Type": day_type,
                "Price": price
            })

df = pd.DataFrame(results)

# Pivot table for better readability
# Columns: Weekday, Weekend
pivot_df = df.pivot_table(index=["Month", "Slot Type"], columns="Day Type", values="Price").reset_index()
# Sort months chronologically
months_order = list(calendar.month_name)[1:]
pivot_df['Month'] = pd.Categorical(pivot_df['Month'], categories=months_order, ordered=True)
pivot_df = pivot_df.sort_values(["Month", "Slot Type"])

out_path = "/Users/darshankanani/.gemini/antigravity-ide/brain/940e9e8a-b234-462c-a9f2-12b3a1ddd11d/final_prediction_matrix.md"

md = ["# 📊 Prediction Matrix - 4 Guests, 0 Lead Days\n"]
md.append("| Month | Slot Type | Weekday Price | Weekend Price |")
md.append("|---|---|---|---|")

for _, r in pivot_df.iterrows():
    md.append(f"| {r['Month']} | {r['Slot Type']} | ₹{r['Weekday']:,.0f} | ₹{r['Weekend']:,.0f} |")

with open(out_path, 'w') as f:
    f.write("\n".join(md))

print(f"Successfully generated matrix to {out_path}")

