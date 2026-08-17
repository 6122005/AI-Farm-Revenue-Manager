import pandas as pd
from app.services.data_pipeline import DataPipeline
from app.services.feature_engineering import FeatureEngineer
from pathlib import Path

data_path = Path("/Users/darshankanani/AI-Farm-Revenue-Manager/backend/data/Farm_Booking_Data_new.xlsx")
df = DataPipeline.load_and_process_file(data_path)
df_feat = FeatureEngineer.process_dataframe(df)

print("=== CONTRADICTIONS IN DATASET ===")

# Example 1: Guest Contradiction
# Let's find same month, same slot, same weekend status, same vacation status
groups = df_feat.groupby(["month", "commercial_slot", "is_weekend", "is_vacation"])
guest_issues = 0
for name, group in groups:
    if len(group) < 2: continue
    
    # Sort by guests ascending
    g_sorted = group.sort_values(by="person_count")
    
    prev_guests = None
    prev_price = None
    prev_date = None
    
    for _, row in g_sorted.iterrows():
        g = row["person_count"]
        p = row["selling_price"]
        d = row["booking_date"]
        
        if prev_guests is not None and g > prev_guests and p < prev_price:
            print(f"Guest Contradiction found in {name}:")
            print(f"  - {prev_date}: {prev_guests} guests paid ₹{prev_price}")
            print(f"  - {d}: {g} guests paid ₹{p} (More guests, but paid LESS!)")
            guest_issues += 1
            if guest_issues > 3: break
            
        prev_guests = g
        prev_price = p
        prev_date = d
    if guest_issues > 3: break

