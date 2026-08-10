import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")
df = pd.read_excel(file_path, sheet_name="Events Export")

df["booking_date"] = pd.to_datetime(df["Start Date"], errors="coerce")
df["selling_price"] = pd.to_numeric(df["Rate"], errors="coerce")

# Handle Guests
cols = [str(c) for c in df.columns]
guests_col = next((c for c in cols if any(k in c.lower() for k in ["person_count", "guest", "person", "pax", "count"])), None)
if guests_col:
    df["person_count"] = pd.to_numeric(df[guests_col], errors="coerce").fillna(10)
else:
    df["person_count"] = 10

df["slot"] = df["Booking Category"].astype(str)
df = df.dropna(subset=["booking_date", "selling_price"])

df["month"] = df["booking_date"].dt.month
df["day_of_week"] = df["booking_date"].dt.dayofweek

def is_weekend(row):
    dow = row['day_of_week']
    s = str(row['slot']).upper()
    if dow == 5 and "NIGHT" in s: return 1
    if dow == 6 and "DAY" in s: return 1
    if dow in [5, 6] and "24H" in s: return 1
    return 0
df["is_weekend"] = df.apply(is_weekend, axis=1)

def normalize_slot(s):
    s = str(s).upper().strip().replace(" ", "_")
    if "24H_NIGHT" in s or "24_HR_NIGHT" in s or "24_HOUR_NIGHT" in s: return "24H_NIGHT"
    return s
df["slot_norm"] = df["slot"].apply(normalize_slot)

# Filter for Aug, Sep, Oct and 24H NIGHT
df = df[df["month"].isin([8, 9, 10])]
df = df[df["slot_norm"] == "24H_NIGHT"]

print("--- 24H NIGHT RAW EXCEL PRICES (No AI, No Guest Adjustment) ---")
for month in [8, 9, 10]:
    print(f"\nMonth: {month}")
    for is_we in [0, 1]:
        subset = df[(df["month"] == month) & (df["is_weekend"] == is_we)]
        label = "Weekend" if is_we else "Weekday"
        if len(subset) == 0:
            print(f"  {label}: 0 Bookings (No Data)")
        else:
            avg_price = subset["selling_price"].mean()
            med_price = subset["selling_price"].median()
            avg_guests = subset["person_count"].mean()
            print(f"  {label}: {len(subset)} Bookings | Average(Mean) = ₹{avg_price:,.0f} | Median = ₹{med_price:,.0f} | Avg Guests = {avg_guests:.1f}")
