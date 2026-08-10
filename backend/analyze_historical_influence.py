import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")

# Load data
df = pd.read_excel(file_path, sheet_name="Events Export")

# Auto-detect columns (based on what we know)
df["booking_date"] = pd.to_datetime(df["Start Date"], errors="coerce")
df["selling_price"] = pd.to_numeric(df["Rate"], errors="coerce")
df["slot"] = df["Booking Category"].astype(str)

df = df.dropna(subset=["booking_date", "selling_price"])

# Extract features
df["year"] = df["booking_date"].dt.year
df["month"] = df["booking_date"].dt.month
df["day_of_week"] = df["booking_date"].dt.dayofweek

# Weekend logic matching slot_engine.py
def is_weekend(row):
    dow = row['day_of_week']
    s = str(row['slot']).upper()
    if dow == 5 and "NIGHT" in s:
        return 1
    if dow == 6 and "DAY" in s:
        return 1
    if dow in [5, 6] and "24H" in s:
        return 1
    return 0

df["is_weekend"] = df.apply(is_weekend, axis=1)

# Normalize slot names to group them properly
def normalize_slot(s):
    s = str(s).upper().strip().replace(" ", "_")
    if "12H_DAY" in s or "12_HR_DAY" in s or "12_HOUR_DAY" in s or "HALF_DAY" in s or "DAY_SLOT" in s:
        return "12H_DAY"
    if "12H_NIGHT" in s or "12_HR_NIGHT" in s or "12_HOUR_NIGHT" in s or "NIGHT_SLOT" in s:
        return "12H_NIGHT"
    if "24H_DAY" in s or "24_HR_DAY" in s or "24_HOUR_DAY" in s or "24H_FULL" in s:
        return "24H_DAY"
    if "24H_NIGHT" in s or "24_HR_NIGHT" in s or "24_HOUR_NIGHT" in s:
        return "24H_NIGHT"
    return s

df["slot_norm"] = df["slot"].apply(normalize_slot)

# Filter for relevant main slots to keep output clean
main_slots = ["12H_DAY", "12H_NIGHT", "24H_DAY", "24H_NIGHT"]
df = df[df["slot_norm"].isin(main_slots)]

# Calculate averages by Year, Month, Slot, Weekend
grouped = df.groupby(["year", "month", "slot_norm", "is_weekend"])["selling_price"].agg(["median", "count"]).reset_index()

# Sort for better readability
grouped = grouped.sort_values(by=["year", "month", "slot_norm", "is_weekend"])

# Save to CSV for easy inspection
grouped.to_csv("historical_price_influence.csv", index=False)

print(f"Total valid records analyzed: {len(df)}")
print("Data saved to historical_price_influence.csv")

# Print a summary of Year-over-Year (YoY) overall increase
yearly_avg = df.groupby("year")["selling_price"].median().reset_index()
print("\n--- Overall Year-by-Year Median Price ---")
print(yearly_avg.to_string(index=False))

# Print May vs Jan comparison to show the seasonality specifically
print("\n--- Month Seasonality (Example: Jan vs May) ---")
month_avg = df[df["month"].isin([1, 5])].groupby(["month"])["selling_price"].median().reset_index()
print(month_avg.to_string(index=False))

# Print a sample of 24H Night across years for May
print("\n--- Deep Dive: 24H_NIGHT in May ---")
may_24h = grouped[(grouped["month"] == 5) & (grouped["slot_norm"] == "24H_NIGHT")]
print(may_24h.to_string(index=False))
