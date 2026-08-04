import sys
sys.path.insert(0, '/Users/darshankanani/AI-Farm-Revenue-Manager/backend')

import pandas as pd
from app.services.prediction_engine import prediction_engine
from datetime import datetime

print("Loading historical data for backtesting...")
df = pd.read_csv('data/clean_booking_data.csv')

# Filter out zero price or extreme outliers that aren't representative of normal backtesting
df = df[df['selling_price'] > 500].copy()

results = []
major_differences = []

print(f"Total historical records to test: {len(df)}")
# We will test all records
count = 0
for idx, row in df.iterrows():
    b_date = str(row['booking_date'])
    # Need to convert booking_date and slot to start_datetime for the request
    # Since we only have commercial_slot like '12H Day', we can infer start time
    slot = row['commercial_slot']
    start_hour = "10:00:00" if "Day" in str(slot) else "18:00:00"
    start_dt = f"{b_date} {start_hour}"
    
    req = {
        "start_datetime": start_dt,
        "slot_type": slot,
        "commercial_slot": slot,
        "person_count": int(row['person_count']),
        "lead_days": int(row['lead_days']) if pd.notna(row.get('lead_days')) else 10
    }
    
    try:
        # Suppress logging for backtest speed
        import logging
        logging.getLogger().setLevel(logging.ERROR)
        
        res = prediction_engine.predict(req, is_batch=True)
        pred_price = res['recommended_price']
        actual_price = row['selling_price']
        
        diff = pred_price - actual_price
        diff_pct = (diff / actual_price) * 100
        
        # Determine if it's a major difference (>30% and >₹1000)
        if abs(diff_pct) > 30 and abs(diff) > 1000:
            major_differences.append({
                "Date": b_date,
                "Slot": slot,
                "Guests": int(row['person_count']),
                "Lead Days": req["lead_days"],
                "Actual Price": actual_price,
                "Predicted Price": pred_price,
                "Diff": diff,
                "Diff %": round(diff_pct, 1)
            })
            
    except Exception as e:
        pass
        
    count += 1
    if count % 50 == 0:
        print(f"Processed {count}/{len(df)} records...")

# Sort by absolute difference
major_differences.sort(key=lambda x: abs(x['Diff']), reverse=True)

# Generate markdown report
md_lines = ["# 🔍 Backtesting: Major Price Differences\n"]
md_lines.append("Testing the current model against historical bookings. Showing records where model prediction deviates by >30% AND >₹1000 from the actual historical price.\n")

md_lines.append(f"**Total Records Tested:** {len(df)}")
md_lines.append(f"**Major Differences Found:** {len(major_differences)}\n")

md_lines.append("| Date | Slot | Guests | Lead Days | Actual Price | Predicted Price | Difference | Difference % |")
md_lines.append("|---|---|---|---|---|---|---|---|")

for row in major_differences[:100]: # Limit to top 100 for readability
    md_lines.append(f"| {row['Date']} | {row['Slot']} | {row['Guests']} | {row['Lead Days']} | ₹{row['Actual Price']:,.0f} | ₹{row['Predicted Price']:,.0f} | ₹{row['Diff']:,.0f} | {row['Diff %']:+.1f}% |")

out_path = "/Users/darshankanani/.gemini/antigravity-ide/brain/fa56f9b0-cebd-475a-8546-69b005a62f3d/backtest_report.md"
with open(out_path, "w") as f:
    f.write("\n".join(md_lines))

print(f"Done! Artifact created at {out_path}")
