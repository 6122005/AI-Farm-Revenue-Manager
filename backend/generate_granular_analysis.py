import pandas as pd
from pathlib import Path

file_path = Path("data/Farm_Booking_Data_new.xlsx")

# Load data
df = pd.read_excel(file_path, sheet_name="Events Export")

df["booking_date"] = pd.to_datetime(df["Start Date"], errors="coerce")
df["selling_price"] = pd.to_numeric(df["Rate"], errors="coerce")
df["slot"] = df["Booking Category"].astype(str)

df = df.dropna(subset=["booking_date", "selling_price"])

df["year"] = df["booking_date"].dt.year
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

main_slots = ["12H_DAY", "12H_NIGHT", "24H_DAY", "24H_NIGHT"]
df = df[df["slot_norm"].isin(main_slots)]
df = df[df["year"] >= 2024]

# Group to get median prices and counts
grouped = df.groupby(["year", "month", "slot_norm", "is_weekend"])["selling_price"].agg(["median", "count"]).reset_index()

# Pivot to get Weekday and Weekend in the same row
pivot_df = grouped.pivot_table(
    index=["year", "month", "slot_norm"], 
    columns="is_weekend", 
    values=["median", "count"]
).reset_index()

# Flatten MultiIndex columns
pivot_df.columns = ['_'.join(str(c) for c in col).strip('_') for col in pivot_df.columns.values]
# Columns are now: year, month, slot_norm, count_0, count_1, median_0, median_1
# (0 = Weekday, 1 = Weekend)

out_file = Path("/Users/darshankanani/.gemini/antigravity-ide/brain/049fd405-cbf5-4069-a9ef-bc764cd12ff6/granular_historical_analysis.md")
months = {1:"Jan", 2:"Feb", 3:"Mar", 4:"Apr", 5:"May", 6:"Jun", 7:"Jul", 8:"Aug", 9:"Sep", 10:"Oct", 11:"Nov", 12:"Dec"}

with open(out_file, "w") as f:
    f.write("# Detailed Historical Pricing Analysis (Raw Excel Data)\n\n")
    f.write("This table breaks down your **EXACT historical booking prices** by Year, Month, and Slot, separating Weekdays from Weekends. ")
    f.write("It explicitly shows the `Weekend Influence` (how much extra customers paid on weekends) for every single slice of time.\n\n")
    
    for year in sorted(pivot_df["year"].unique()):
        f.write(f"## Year: {year}\n\n")
        y_df = pivot_df[pivot_df["year"] == year]
        
        for month in sorted(y_df["month"].unique()):
            f.write(f"### {months[month]} {year}\n")
            f.write("| Slot | Weekday Median | Weekday Bookings | Weekend Median | Weekend Bookings | Weekend Influence (Diff) |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            
            m_df = y_df[y_df["month"] == month].sort_values("slot_norm")
            
            for _, row in m_df.iterrows():
                slot = row["slot_norm"].replace("_", " ")
                
                wd_price = row.get("median_0", float('nan'))
                wd_count = row.get("count_0", 0)
                if pd.isna(wd_price) or wd_count == 0:
                    wd_price_str = "No Data"
                    wd_count_str = "0"
                else:
                    wd_price_str = f"₹{wd_price:,.0f}"
                    wd_count_str = str(int(wd_count))
                    
                we_price = row.get("median_1", float('nan'))
                we_count = row.get("count_1", 0)
                if pd.isna(we_price) or we_count == 0:
                    we_price_str = "No Data"
                    we_count_str = "0"
                else:
                    we_price_str = f"₹{we_price:,.0f}"
                    we_count_str = str(int(we_count))
                    
                diff_str = "-"
                if not pd.isna(wd_price) and not pd.isna(we_price) and wd_count > 0 and we_count > 0:
                    diff = we_price - wd_price
                    diff_pct = (diff / wd_price) * 100 if wd_price > 0 else 0
                    sign = "+" if diff > 0 else ""
                    diff_str = f"{sign}₹{diff:,.0f} ({sign}{diff_pct:.1f}%)"
                    
                f.write(f"| {slot} | {wd_price_str} | {wd_count_str} | {we_price_str} | {we_count_str} | **{diff_str}** |\n")
            f.write("\n")

print("Done. Wrote to granular_historical_analysis.md")
