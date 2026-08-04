import pandas as pd
import calendar

# 1. Load predicted data
predicted_data = """
Month	Slot Type	Weekday Price	Weekend Price
January	12H Day	3100	2500
January	12H Night	2600	2600
January	24H Day	4800	4800
January	24H Night	3900	5000
February	12H Day	2600	2900
February	12H Night	2300	2500
February	24H Day	4400	4900
February	24H Night	3600	4800
March	12H Day	3600	3600
March	12H Night	2900	2900
March	24H Day	6100	6100
March	24H Night	4900	6300
April	12H Day	3900	3900
April	12H Night	3400	3300
April	24H Day	6500	6800
April	24H Night	5000	11800
May	12H Day	3600	3600
May	12H Night	2800	2900
May	24H Day	6100	7200
May	24H Night	5900	11800
June	12H Day	3600	3600
June	12H Night	2800	3000
June	24H Day	5500	6000
June	24H Night	5300	7800
July	12H Day	3100	3100
July	12H Night	2500	2900
July	24H Day	5200	5500
July	24H Night	3700	5000
August	12H Day	2100	2100
August	12H Night	2700	2800
August	24H Day	5400	5500
August	24H Night	4800	4800
September	12H Day	2800	2800
September	12H Night	2700	2900
September	24H Day	4500	4900
September	24H Night	4500	4700
October	12H Day	2600	2600
October	12H Night	2900	3000
October	24H Day	5000	5100
October	24H Night	4000	4600
November	12H Day	3100	3000
November	12H Night	2300	2300
November	24H Day	4800	4800
November	24H Night	4200	4700
December	12H Day	2800	3100
December	12H Night	2800	2800
December	24H Day	5300	5300
December	24H Night	4800	5400
"""

lines = predicted_data.strip().split('\n')[1:]
pred_dict = {}
for line in lines:
    parts = line.split('\t')
    m, s, wd, we = parts[0], parts[1], float(parts[2]), float(parts[3])
    pred_dict[(m, s, 'Weekday')] = wd
    pred_dict[(m, s, 'Weekend')] = we

# 2. Load clean data for raw averages
df = pd.read_csv('data/clean_booking_data.csv')

def get_month_name(m_num):
    return calendar.month_name[m_num]

df['month_name'] = df['month'].apply(get_month_name)
df['day_type'] = df['is_weekend'].apply(lambda x: 'Weekend' if x == 1 else 'Weekday')

# Calculate raw averages
grouped = df.groupby(['month_name', 'commercial_slot', 'day_type']).agg({
    'selling_price': 'mean',
    'person_count': 'mean',
    'month': 'count'
}).reset_index()

grouped.rename(columns={'month': 'records_count'}, inplace=True)

# 3. Compare and format markdown table
md_lines = ["# 📊 Raw Averages vs Model Predictions (10 Guests) Comparison\n"]
md_lines.append("| Month | Slot Type | Day Type | Raw Avg Price | Raw Avg Guests | Records | Model Predicted Price (10 Guests) | Difference (Model - Raw) | Analysis |")
md_lines.append("|---|---|---|---|---|---|---|---|---|")

months_order = list(calendar.month_name)[1:]

for month in months_order:
    for slot in ["12H Day", "12H Night", "24H Day", "24H Night"]:
        for day_type in ["Weekday", "Weekend"]:
            
            # Get raw stats
            raw_row = grouped[(grouped['month_name'] == month) & (grouped['commercial_slot'] == slot) & (grouped['day_type'] == day_type)]
            
            if not raw_row.empty:
                raw_price = raw_row['selling_price'].values[0]
                raw_guests = raw_row['person_count'].values[0]
                records = raw_row['records_count'].values[0]
            else:
                raw_price = 0
                raw_guests = 0
                records = 0
                
            pred_price = pred_dict.get((month, slot, day_type), 0)
            
            if raw_price > 0:
                diff = pred_price - raw_price
                diff_pct = (diff / raw_price) * 100
                
                # Simple analysis
                if records < 5:
                    analysis = "Sparse data fallback used"
                elif diff > 0 and raw_guests < 10:
                    analysis = "Model added extra guest charge"
                elif diff < 0 and raw_guests > 10:
                    analysis = "Model reduced price for lower guests"
                else:
                    analysis = "Aligned with historical median + guest calc"
                
                md_lines.append(f"| {month} | {slot} | {day_type} | ₹{raw_price:,.0f} | {raw_guests:.1f} | {records} | ₹{pred_price:,.0f} | ₹{diff:,.0f} ({diff_pct:+.1f}%) | {analysis} |")

out_path = "/Users/darshankanani/.gemini/antigravity-ide/brain/fa56f9b0-cebd-475a-8546-69b005a62f3d/raw_vs_predicted.md"
with open(out_path, "w") as f:
    f.write("\n".join(md_lines))
print(f"Artifact created at {out_path}")
