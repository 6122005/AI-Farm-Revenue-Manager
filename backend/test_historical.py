import pandas as pd
from app.services.prediction_engine import prediction_engine
import numpy as np

# Load data
df = pd.read_csv('data/clean_booking_data.csv')

# Filter out festivals and relatives
# Assuming 'is_festival' == 0 and 'selling_price' > 500 (relatives often pay 0 or very little)
filtered_df = df[
    (df['is_festival'] == 0) & 
    (df['selling_price'] >= 500) &
    (~df['festival_name'].astype(str).str.lower().str.strip().isin(['makar sankranti', 'holi', 'dhuleti']))
].copy()

results = []
count = 0
total = len(filtered_df)

print(f"Total valid historical records to test: {total}")

for idx, row in filtered_df.iterrows():
    # Build prediction request
    try:
        req = {
            "start_datetime": f"{row['booking_date']} 10:00", # exact time doesn't matter much if slot is given
            "slot_type": row['commercial_slot'],
            "commercial_slot": row['commercial_slot'],
            "person_count": int(row['person_count']),
            "lead_days": float(row.get('lead_days', 10)),
        }
        
        # Predict
        res = prediction_engine.predict(req, is_batch=True)
        pred_price = res.get('recommended_price', 0)
        actual_price = row['selling_price']
        
        diff = pred_price - actual_price
        diff_pct = (diff / actual_price) * 100 if actual_price > 0 else 0
        
        # Only log major differences: > 30% or > 2000 Rs
        if abs(diff) > 2000 or abs(diff_pct) > 30:
            results.append({
                "Date": row['booking_date'],
                "Slot": row['commercial_slot'],
                "Guests": row['person_count'],
                "Actual Price": actual_price,
                "Predicted Price": pred_price,
                "Diff": diff,
                "Diff %": diff_pct
            })
            
    except Exception as e:
        print(f"Error on {row['booking_date']}: {e}")
        
    count += 1
    if count % 100 == 0:
        print(f"Processed {count}/{total}")

res_df = pd.DataFrame(results)
if not res_df.empty:
    res_df = res_df.sort_values(by="Diff %", ascending=False)
    out_path = "/Users/darshankanani/.gemini/antigravity-ide/brain/fa56f9b0-cebd-475a-8546-69b005a62f3d/major_differences.md"
    
    md = ["# 🚨 Major Prediction Differences (Historical vs Model)\n"]
    md.append("This table shows ONLY records where the predicted price differs by **more than 30%** or **₹2,000** from the actual historical price.\n")
    md.append("| Date | Slot | Guests | Actual Price | Predicted Price | Diff | Diff % |")
    md.append("|---|---|---|---|---|---|---|")
    
    for _, r in res_df.iterrows():
        md.append(f"| {r['Date']} | {r['Slot']} | {r['Guests']} | ₹{r['Actual Price']:,.0f} | ₹{r['Predicted Price']:,.0f} | ₹{r['Diff']:,.0f} | {r['Diff %']:+.1f}% |")
        
    with open(out_path, 'w') as f:
        f.write("\n".join(md))
    print(f"Saved {len(res_df)} major differences to {out_path}")
else:
    print("No major differences found!")
