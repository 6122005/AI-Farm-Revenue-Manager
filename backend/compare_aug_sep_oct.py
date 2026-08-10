import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")
df = pd.read_excel(file_path, sheet_name="Events Export")

df["booking_date"] = pd.to_datetime(df["Start Date"], errors="coerce")
df["selling_price"] = pd.to_numeric(df["Rate"], errors="coerce")

# Find the guest column dynamically just like pipeline does
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
    if "12H_DAY" in s or "12_HR_DAY" in s or "12_HOUR_DAY" in s or "HALF_DAY" in s or "DAY_SLOT" in s: return "12H_DAY"
    if "12H_NIGHT" in s or "12_HR_NIGHT" in s or "12_HOUR_NIGHT" in s or "NIGHT_SLOT" in s: return "12H_NIGHT"
    if "24H_DAY" in s or "24_HR_DAY" in s or "24_HOUR_DAY" in s or "24H_FULL" in s: return "24H_DAY"
    if "24H_NIGHT" in s or "24_HR_NIGHT" in s or "24_HOUR_NIGHT" in s: return "24H_NIGHT"
    return s
df["slot_norm"] = df["slot"].apply(normalize_slot)

# Filter for Aug, Sep, Oct
df = df[df["month"].isin([8, 9, 10])]
df = df[df["slot_norm"].isin(["12H_DAY", "12H_NIGHT", "24H_DAY", "24H_NIGHT"])]

def calc_guest_adjustment(anchor_guests, target_guests=10):
    diff = target_guests - anchor_guests
    if diff == 0: return 0.0
    
    adj = 0.0
    if diff > 0:
        for i in range(int(anchor_guests) + 1, int(target_guests) + 1):
            if i <= 15: adj += 62.5
            else: adj += 100.0
    else:
        for i in range(int(target_guests) + 1, int(anchor_guests) + 1):
            if i <= 15: adj -= 62.5
            else: adj -= 100.0
    return adj

results = []

for month in [8, 9, 10]:
    for slot in ["12H_DAY", "12H_NIGHT", "24H_DAY", "24H_NIGHT"]:
        for is_we in [0, 1]:
            subset = df[(df["month"] == month) & (df["slot_norm"] == slot) & (df["is_weekend"] == is_we)]
            
            if len(subset) == 0:
                results.append({
                    "Month": month,
                    "Slot": slot,
                    "Is_Weekend": is_we,
                    "Raw_Median": 0,
                    "Anchor_Guests": 0,
                    "Guest_Adj": 0,
                    "Final_Pure_Price": 0,
                    "Count": 0
                })
                continue
                
            raw_median = subset["selling_price"].median()
            anchor_guests = subset["person_count"].mean()
            guest_adj = calc_guest_adjustment(anchor_guests, 10)
            
            results.append({
                "Month": month,
                "Slot": slot,
                "Is_Weekend": is_we,
                "Raw_Median": raw_median,
                "Anchor_Guests": anchor_guests,
                "Guest_Adj": guest_adj,
                "Final_Pure_Price": raw_median + guest_adj,
                "Count": len(subset)
            })

res_df = pd.DataFrame(results)

# Now, compare with AI's prices that user provided
ai_prices = {
    # August
    (8, "12H_DAY", 0): 3070, (8, "12H_DAY", 1): 3580,
    (8, "12H_NIGHT", 0): 2460, (8, "12H_NIGHT", 1): 2480,
    (8, "24H_DAY", 0): 3770, (8, "24H_DAY", 1): 3500,
    (8, "24H_NIGHT", 0): 3560, (8, "24H_NIGHT", 1): 4500,
    # September
    (9, "12H_DAY", 0): 2370, (9, "12H_DAY", 1): 3580,
    (9, "12H_NIGHT", 0): 2590, (9, "12H_NIGHT", 1): 2910,
    (9, "24H_DAY", 0): 3660, (9, "24H_DAY", 1): 3310,
    (9, "24H_NIGHT", 0): 4490, (9, "24H_NIGHT", 1): 4250,
    # October
    (10, "12H_DAY", 0): 2790, (10, "12H_DAY", 1): 3260,
    (10, "12H_NIGHT", 0): 2470, (10, "12H_NIGHT", 1): 3780,
    (10, "24H_DAY", 0): 3670, (10, "24H_DAY", 1): 4130,
    (10, "24H_NIGHT", 0): 3880, (10, "24H_NIGHT", 1): 4500,
}

comparison = []
for _, r in res_df.iterrows():
    ai_p = ai_prices.get((r["Month"], r["Slot"], r["Is_Weekend"]), 0)
    diff = ai_p - r["Final_Pure_Price"]
    comparison.append({
        "Month": r["Month"],
        "Slot": r["Slot"].replace("_", " "),
        "Is_Weekend": "Weekend" if r["Is_Weekend"] else "Weekday",
        "Count": r["Count"],
        "Pure_Excel_Price": round(r["Final_Pure_Price"]),
        "AI_Price": round(ai_p),
        "Difference": round(diff)
    })

comp_df = pd.DataFrame(comparison)
print(comp_df.to_string(index=False))

# Identify slices with 0 or very few bookings
print("\n--- Low Data Segments (Count < 3) ---")
print(comp_df[comp_df["Count"] < 3].to_string(index=False))
