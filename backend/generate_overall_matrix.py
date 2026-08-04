import pandas as pd
import numpy as np

df = pd.read_excel('data/Farm_Booking_Data_new.xlsx', sheet_name='Events Export')

# Fix time parsing issue first to get correct slots
slots = []
for idx, row in df.iterrows():
    h_val = 12
    val = str(row.get('Start Time', ''))
    if pd.notna(val) and val.strip():
        if ' ' in val:
            val = val.split(' ')[1]
        try:
            h_val = int(val.split(':')[0])
        except:
            pass
    
    is_daytime = (6 <= h_val < 18)
    dur = 24.0
    dur_str = str(row.get('Duration', '')).lower()
    if '12' in dur_str:
        dur = 12.0
    
    if dur == 12.0:
        slots.append("12H Day" if is_daytime else "12H Night")
    else:
        slots.append("24H Day" if is_daytime else "24H Night")

df['Slot'] = slots
summary = df.groupby(['Slot', 'Weekend'])['Rate'].median().unstack()
summary.columns = ['Weekday Price', 'Weekend Price']

# Format to markdown
md_str = "# Historical Baseline Matrix (From Farm_Booking_Data_new.xlsx)\n\n"
md_str += "| Slot | Historical Weekday Median (₹) | Historical Weekend Median (₹) |\n|---|---|---|\n"
slot_order = ["12H Day", "12H Night", "24H Day", "24H Night", "Couple Full Day"]
for slot in slot_order:
    if slot in summary.index:
        wkday = summary.loc[slot, 'Weekday Price'] if 'Weekday Price' in summary.columns and pd.notna(summary.loc[slot, 'Weekday Price']) else 0
        wkend = summary.loc[slot, 'Weekend Price'] if 'Weekend Price' in summary.columns and pd.notna(summary.loc[slot, 'Weekend Price']) else wkday
        md_str += f"| {slot} | ₹{int(wkday)} | ₹{int(wkend)} |\n"

with open('/Users/darshankanani/.gemini/antigravity-ide/brain/fa56f9b0-cebd-475a-8546-69b005a62f3d/historical_baseline_matrix.md', 'w') as f:
    f.write(md_str)
print("Done")
