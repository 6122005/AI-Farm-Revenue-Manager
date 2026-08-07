import pandas as pd
import numpy as np
df = pd.read_excel("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx", sheet_name="Events Export")
# Basic mapping
df["price"] = pd.to_numeric(df["Rate"], errors="coerce")
df["date"] = pd.to_datetime(df["Start Date"], errors="coerce")
df["month"] = df["date"].dt.month
df["day_of_week"] = df["date"].dt.dayofweek
df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
df["slot"] = df["Booking Category"]
df["person_count"] = pd.to_numeric(df["Number of Guests"], errors="coerce").fillna(4)

# Filter for August (8) and September (9) and 24H Night
for m in [8, 9]:
    print(f"\n--- Month {m} ---")
    df_m = df[(df["month"] == m) & (df["slot"] == "24H Night")]
    
    # Weekday vs Weekend
    for w, name in [(0, "Weekday"), (1, "Weekend")]:
        df_w = df_m[df_m["is_weekend"] == w]
        if len(df_w) == 0:
            print(f"{name}: No bookings")
            continue
            
        avg_price = df_w["price"].mean()
        med_price = df_w["price"].median()
        
        prices = df_w["price"].values
        mad = np.median(np.abs(prices - med_price))
        if mad > 0:
            is_outlier = np.abs(prices - med_price) > (3 * mad)
            prices = prices[~is_outlier]
        trimmed_mean = np.mean(prices)
        
        avg_guests = df_w["person_count"].mean()
        count = len(df_w)
        
        # Calculate raw vs normalized
        extra_guests = np.maximum(0, df_w["person_count"] - 4)
        marginal_cost = 1000.0  # 24H
        norm_price = df_w["price"] - (extra_guests * marginal_cost)
        
        avg_norm = norm_price.mean()
        
        print(f"{name} ({count} bookings):")
        print(f"  Raw Average Price: {avg_price:.2f}")
        print(f"  Raw Median Price: {med_price:.2f}")
        print(f"  Trimmed Mean (Model's Base): {trimmed_mean:.2f}")
        print(f"  Average Guests: {avg_guests:.2f}")
        print(f"  Normalized Base Price (for 4 guests): {avg_norm:.2f}")
