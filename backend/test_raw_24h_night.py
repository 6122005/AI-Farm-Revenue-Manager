import pandas as pd
from app.config import DATA_DIR
path = DATA_DIR / "Farm_Booking_Data_new.xlsx"
df = pd.read_excel(path, sheet_name="Events Export")

print("Raw columns:", list(df.columns))

# Let's see the unique slots
slots = df['Booking Category'].unique()
print("Unique slots in raw file:", slots)

# Let's filter for anything with 24 and Night
mask = df['Booking Category'].str.contains('24', na=False) & df['Booking Category'].str.contains('Night', na=False, case=False)
df_24n = df[mask]
print(f"Found {len(df_24n)} rows matching '24...Night'")

# Let's just find anything with '24'
mask24 = df['Booking Category'].str.contains('24', na=False)
print("Unique '24' slots:", df[mask24]['Booking Category'].unique())

for slot_name in df[mask24]['Booking Category'].unique():
    subset = df[df['Booking Category'] == slot_name]
    avg = subset['Rate'].mean()
    med = subset['Rate'].median()
    print(f"Slot '{slot_name}': Count={len(subset)}, Avg Rate={avg}, Med Rate={med}")
