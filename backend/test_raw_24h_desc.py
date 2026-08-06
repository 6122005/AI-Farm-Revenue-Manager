import pandas as pd
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = pd.read_excel(path, sheet_name="Events Export")

for col in ['Title', 'Description', 'Booking Category']:
    if col in df.columns:
        mask = df[col].astype(str).str.contains('24', case=False, na=False)
        print(f"Rows containing '24' in {col}: {len(df[mask])}")
        
mask_start = df['Start Time'].astype(str).str.contains('24', na=False)
mask_end = df['End Time'].astype(str).str.contains('24', na=False)
print("Start time contains 24:", len(df[mask_start]))

# How about duration > 12 hours? Let's parse Start Time and End Time!
count = 0
prices = []
for idx, row in df.iterrows():
    st = str(row['Start Time'])
    et = str(row['End Time'])
    # If they are exactly the same, maybe it's 24 hours?
    if st != 'nan' and et != 'nan' and st == et:
        count += 1
        prices.append(row['Rate'])

print(f"Start Time == End Time count: {count}")
if count > 0:
    print(f"Average rate for these: {sum(prices)/count}")
