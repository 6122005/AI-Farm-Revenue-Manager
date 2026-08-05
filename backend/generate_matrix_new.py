from app.services.prediction_engine import prediction_engine
import pandas as pd
import calendar
from datetime import datetime

year = 2026
slots = ["12H Day", "12H Night", "24H Day", "24H Night"]

# Helper to find a specific weekday/weekend in a month
def get_sample_date(month, is_weekend):
    # Weekday: Tuesday (1), Weekend: Saturday (5)
    target_day = 5 if is_weekend else 1
    for day in range(1, 28):
        dt = datetime(year, month, day)
        if dt.weekday() == target_day:
            return dt.strftime("%Y-%m-%d 10:00")
    return None

results = []

for month in range(1, 13):
    month_name = calendar.month_name[month]
    for slot in slots:
        for is_weekend in [0, 1]:
            dt_str = get_sample_date(month, is_weekend)
            req = {
                "start_datetime": dt_str,
                "commercial_slot": slot,
                "person_count": 10,
                "lead_days": 10
            }
            try:
                res = prediction_engine.predict(req, is_batch=False)
                price = res.get("recommended_price", 0)
            except Exception as e:
                price = 0
                print(f"Error on {month_name} {slot}: {e}")
                
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

out_path = "/Users/darshankanani/.gemini/antigravity-ide/brain/fa56f9b0-cebd-475a-8546-69b005a62f3d/new_prediction_matrix.md"

md = ["# 📊 Prediction Matrix (New Engine) - 10 Guests, 10 Lead Days\n"]
md.append("| Month | Slot Type | Weekday Price | Weekend Price |")
md.append("|---|---|---|---|")

for _, r in pivot_df.iterrows():
    md.append(f"| {r['Month']} | {r['Slot Type']} | ₹{r['Weekday']:,.0f} | ₹{r['Weekend']:,.0f} |")

with open(out_path, 'w') as f:
    f.write("\n".join(md))

print(f"Successfully generated matrix to {out_path}")

